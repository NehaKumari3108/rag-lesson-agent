import argparse, os, re
from pathlib import Path

from dotenv import load_dotenv


def main(argv=None):
    load_dotenv()
    p = argparse.ArgumentParser(prog="lesson-agent", description="Self-evaluating lesson generator")
    sub = p.add_subparsers(dest="cmd")
    r = sub.add_parser("run", help="generate -> evaluate -> regenerate")
    r.add_argument("--topic", default="Introduction to RAG (Retrieval-Augmented Generation)")
    r.add_argument("--inject-error", action="store_true", help="demo: plant errors in draft 1")
    r.add_argument("--max-retries", type=int, default=int(os.getenv("MAX_RETRIES", 2)))
    r.add_argument("--facts", default=None, help="path to a reference-facts file for the topic")
    r.add_argument("--out", default=None)
    f = sub.add_parser("feedback", help="store human feedback; used in all future generations")
    f.add_argument("text")
    a = p.parse_args(argv)
    from .memory import Memory
    mem = Memory(os.getenv("MEMORY_PATH", "memory/memory.json"))
    if a.cmd == "feedback":
        mem.add_feedback(a.text); print("feedback saved"); return
    a = p.parse_args(["run"] + (argv or [])) if a.cmd is None else a
    from .graph import Ctx, build_graph
    from .llm import build_llm
    from .rubric import load_facts, load_rubric
    slug = re.sub(r"[^a-z0-9]+", "-", a.topic.lower()).strip("-")[:40]
    ctx = Ctx(gen=build_llm("gen"), judge=build_llm("judge"), memory=mem, rubric=load_rubric(),
              facts=load_facts(a.facts), out_dir=Path(a.out or f"outputs/{slug}"),
              max_retries=a.max_retries, inject_error=a.inject_error)
    st = build_graph(ctx).invoke({"topic": a.topic})
    return st


if __name__ == "__main__":
    main()
