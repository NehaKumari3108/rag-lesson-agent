"""Persistent memory: run history, per-check failure stats, learned generator rules, human feedback."""
import json, time
from pathlib import Path

MAX_RULES, MAX_FEEDBACK = 8, 5


class Memory:
    def __init__(self, path):
        self.path = Path(path)
        self.d = {"runs": [], "check_stats": {}, "learned_rules": [], "human_feedback": []}
        if self.path.exists():
            self.d.update(json.loads(self.path.read_text()))

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.d, indent=2))

    def guidelines(self):
        rules = [r["rule"] for r in self.d["learned_rules"]]
        fb = [f"Human feedback: {f['text']}" for f in self.d["human_feedback"][-MAX_FEEDBACK:]]
        return rules + fb

    def add_feedback(self, text):
        self.d["human_feedback"].append({"text": text, "ts": time.strftime("%Y-%m-%d %H:%M")})
        self.save()

    def record_run(self, topic, status, attempts, failed_ids, all_ids):
        """Update stats. A check 'fails' in a run if it failed on ANY attempt of that run."""
        for cid in all_ids:
            s = self.d["check_stats"].setdefault(cid, {"runs": 0, "fails": 0})
            s["runs"] += 1
            s["fails"] += int(cid in failed_ids)
        self.d["runs"].append({"ts": time.strftime("%Y-%m-%d %H:%M"), "topic": topic, "status": status,
                               "attempts": attempts, "failed_checks": sorted(failed_ids)})

    def add_rules(self, rules):
        have = {r["rule"].lower() for r in self.d["learned_rules"]}
        for r in rules:
            if r["rule"].lower() not in have:
                self.d["learned_rules"].append({"rule": r["rule"], "source_check": r["check_id"],
                                                "added": time.strftime("%Y-%m-%d")})
        self.d["learned_rules"] = self.d["learned_rules"][-MAX_RULES:]  # bounded: prompt never bloats

    def rubric_review_flags(self):
        """Checks failing often get FLAGGED for a human; the rubric is never auto-edited (avoids evaluator drift)."""
        return [cid for cid, s in self.d["check_stats"].items() if s["fails"] >= 3 and s["fails"] / s["runs"] >= 0.4]
