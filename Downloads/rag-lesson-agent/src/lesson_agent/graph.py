"""LangGraph pipeline:  load_memory -> generate -> evaluate -+-> finalize -> evolve -> END
                                                      ^      |
                                                      +-rewrite (only on FAIL and retries left)"""
import difflib, json, re
from dataclasses import dataclass
from pathlib import Path
from typing import List, TypedDict

from langgraph.graph import END, START, StateGraph

from .rubric import evaluate

GEN_SYSTEM = """ROLE:GENERATE
You are a teacher writing a standalone beginner lesson.
Audience: a 12th-grade graduate from India, limited English vocabulary, non-English-medium school, zero background, wants to start an AI career.
Hard requirements (the lesson is graded pass/fail on each):
1. Use these Markdown headings: What is it? / Why does it matter? / How does it work? / Example / Limits / Recap and quick check.
2. Short sentences (average under 15 words, none over 28). Simple everyday words. No idioms, no buzzwords.
3. Define every technical term in the sentence where it first appears ("X means ...", "X stands for ...").
4. Include one everyday analogy AND one concrete question walked through step by step.
5. Cover what it is, why it matters, how it works, and at least one limit. 600-1000 words.
6. Never state anything you are not sure is true. Use the REFERENCE FACTS.
Output ONLY the lesson inside <lesson></lesson> tags."""

REWRITE_SYSTEM = """ROLE:REWRITE
You are fixing a lesson that FAILED review. Make the SMALLEST edits that fix every failed check.
Keep every part that already passed. Do not rewrite the whole lesson.
Output exactly:
<changes>
- bullet list: what you changed and which check id it fixes
</changes>
<lesson>
the full corrected lesson
</lesson>"""

FALSE_CLAIM = ("Every time you ask a question, RAG retrains the whole model on all your documents. "
               "This changes the model's parameters, so the model slowly forgets everything else it knew.")
JARGON = ("Internally, the retriever computes cosine similarity between high-dimensional dense embeddings "
          "and uses ANN indices to leverage the vector database.")


class State(TypedDict, total=False):
    topic: str
    guidelines: List[str]
    draft: str
    attempt: int
    results: list
    passed: bool
    rejections: list
    all_failed_ids: list
    status: str


@dataclass
class Ctx:
    gen: object
    judge: object
    memory: object
    rubric: list
    facts: str
    out_dir: Path
    max_retries: int = 2
    inject_error: bool = False


def _tag(text, tag):
    m = re.search(rf"<{tag}>\s*(.*?)\s*</{tag}>", text, re.S)
    return m.group(1).strip() if m else None


def inject_flaws(md: str) -> str:
    """DEMO ONLY: plant a false claim + deep jargon in the first draft to prove the evaluator catches errors."""
    lines = md.splitlines()
    for i, l in enumerate(lines):
        if l.startswith("#") and "how" in l.lower():
            lines[i + 1:i + 1] = ["", FALSE_CLAIM, JARGON]
            return "\n".join(lines)
    return md + f"\n\n{FALSE_CLAIM} {JARGON}\n"


def build_graph(c: Ctx):
    def load_memory(s):
        g = c.memory.guidelines()
        print(f"[memory] {len(g)} learned guideline(s) loaded")
        return {"guidelines": g, "attempt": 0, "rejections": [], "all_failed_ids": []}

    def generate(s):
        extra = ("\n\nLEARNED GUIDELINES (from past failures/feedback):\n- " + "\n- ".join(s["guidelines"])) if s["guidelines"] else ""
        user = f"Topic: {s['topic']}\n\nREFERENCE FACTS:\n{c.facts}{extra}"
        draft = _tag(c.gen.complete(GEN_SYSTEM, user), "lesson") or ""
        if c.inject_error:
            draft = inject_flaws(draft)
            print("[demo] deliberate errors injected into draft 1 (false claim + jargon)")
        print(f"[generate] draft 1 ({len(draft.split())} words)")
        return {"draft": draft, "attempt": 1}

    def evaluate_node(s):
        res = evaluate(c.judge, s["draft"], c.facts, c.rubric)
        failed = [r for r in res if not r["passed"]]
        print(f"[evaluate] attempt {s['attempt']}: " + " ".join(f"{r['id']}={'PASS' if r['passed'] else 'FAIL'}" for r in res))
        upd = {"results": res, "passed": not failed}
        if failed:
            for r in failed:
                print(f"    x {r['id']} ({r['dimension']}): {r['reason']}")
            upd["rejections"] = s["rejections"] + [{"attempt": s["attempt"], "failed": failed, "changes": None}]
            upd["all_failed_ids"] = sorted(set(s["all_failed_ids"]) | {r["id"] for r in failed})
        return upd

    def route(s):
        if s["passed"]:
            return "finalize"
        return "rewrite" if s["attempt"] <= c.max_retries else "finalize"  # guaranteed termination

    def rewrite(s):
        fails = s["rejections"][-1]["failed"]
        brief = "\n".join(f"- {f['id']} [{f['dimension']}]: {f['reason']}\n  evidence: {f['evidence'] or 'n/a'}\n  fix: {f['fix_hint']}" for f in fails)
        user = (f"Topic: {s['topic']}\n\nFAILED CHECKS:\n{brief}\n\nREFERENCE FACTS:\n{c.facts}\n\n"
                f"CURRENT LESSON:\n<lesson>\n{s['draft']}\n</lesson>")
        out = c.gen.complete(REWRITE_SYSTEM, user)
        new = _tag(out, "lesson") or s["draft"]
        changes = _tag(out, "changes") or "(model gave no change list)"
        diff = [l for l in difflib.unified_diff(s["draft"].splitlines(), new.splitlines(), lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
        rej = s["rejections"][:-1] + [{**s["rejections"][-1], "changes": changes,
                                       "diff_lines": f"+{sum(l[0]=='+' for l in diff)} / -{sum(l[0]=='-' for l in diff)}"}]
        print(f"[rewrite] attempt {s['attempt'] + 1}: {len(diff)} changed line(s)")
        return {"draft": new, "attempt": s["attempt"] + 1, "rejections": rej}

    def finalize(s):
        status = "PASSED" if s["passed"] else "NEEDS_HUMAN_REVIEW"
        c.out_dir.mkdir(parents=True, exist_ok=True)
        name = "lesson.md" if s["passed"] else "lesson.NEEDS_REVIEW.md"  # unverified content is never named 'lesson.md'
        (c.out_dir / name).write_text(s["draft"])
        (c.out_dir / "rejection_log.json").write_text(json.dumps(s["rejections"], indent=2))
        (c.out_dir / "rejection_log.md").write_text(render_log(s, status))
        (c.out_dir / "final_scorecard.json").write_text(json.dumps(s["results"], indent=2))
        print(f"[finalize] {status} after {s['attempt']} draft(s) -> {c.out_dir / name}")
        return {"status": status}

    def evolve(s):
        c.memory.record_run(s["topic"], s["status"], s["attempt"], set(s["all_failed_ids"]), [r["id"] for r in c.rubric])
        if s["rejections"]:
            fails = {}
            for rej in s["rejections"]:
                for f in rej["failed"]:
                    fails.setdefault(f["id"], f)
            user = "\n".join(f"CHECK {i}: {f['dimension']} | reason: {f['reason']} | evidence: {f['evidence']}" for i, f in fails.items())
            raw = c.gen.complete("ROLE:REFLECT\nYou improve a lesson generator. For each failed check write ONE short imperative rule "
                                 "(max 25 words) that would stop the generator making this mistake next time. "
                                 'Return ONLY JSON: {"rules":[{"check_id":"J1","rule":"..."}]}', user)
            try:
                c.memory.add_rules(json.loads(raw[raw.index("{"): raw.rindex("}") + 1])["rules"])
            except Exception:
                print("[evolve] reflection unparseable, skipped (no memory damage)")
        flags = c.memory.rubric_review_flags()
        if flags:
            print(f"[evolve] checks {flags} fail often -> flagged for HUMAN rubric review (rubric is never auto-edited)")
        c.memory.save()
        print(f"[evolve] memory saved ({len(c.memory.d['learned_rules'])} rule(s), {len(c.memory.d['runs'])} run(s))")
        return {}

    g = StateGraph(State)
    for n, f in [("load_memory", load_memory), ("generate", generate), ("evaluate", evaluate_node),
                 ("rewrite", rewrite), ("finalize", finalize), ("evolve", evolve)]:
        g.add_node(n, f)
    g.add_edge(START, "load_memory"); g.add_edge("load_memory", "generate"); g.add_edge("generate", "evaluate")
    g.add_conditional_edges("evaluate", route, {"rewrite": "rewrite", "finalize": "finalize"})
    g.add_edge("rewrite", "evaluate"); g.add_edge("finalize", "evolve"); g.add_edge("evolve", END)
    return g.compile()


def render_log(s, status):
    L = [f"# Rejection log: {s['topic']}", f"**Final status: {status}** (drafts produced: {s['attempt']})", ""]
    if not s["rejections"]:
        L.append("Draft 1 passed every check. Nothing was rejected.")
    for r in s["rejections"]:
        L.append(f"## Draft {r['attempt']} REJECTED")
        for f in r["failed"]:
            L.append(f"- **{f['id']}** ({f['dimension']}) — {f['reason']}" + (f"\n  - evidence: `{f['evidence']}`" if f["evidence"] else ""))
        if r.get("changes"):
            L.append(f"\n**What changed on retry** ({r.get('diff_lines', '')} lines):\n{r['changes']}")
        else:
            L.append("\n_No retry left; sent to human review._")
        L.append("")
    return "\n".join(L)
