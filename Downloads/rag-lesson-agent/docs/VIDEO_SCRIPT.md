# Loom script (target 17 min, face camera ON the whole time)

**0:00-2:00 Intro (face).** Who you are, the problem: "not one clever prompt, a loop that decides if content is good enough."
**2:00-5:00 Architecture.** Show README diagram. Walk nodes: load_memory, generate, evaluate, rewrite, finalize, evolve. Say WHY LangGraph.
**5:00-8:00 The rubric.** Open rubric.yaml. Explain hybrid design: 5 code checks vs 5 LLM checks, fail-closed, grounding facts, separate judge.
**8:00-12:00 Live run, normal.** `python -m lesson_agent run`. Narrate each node's log line. Open outputs/.../lesson.md and final_scorecard.json.
**12:00-15:00 Deliberate error.** `python -m lesson_agent run --inject-error`. Point at: false claim "RAG retrains the whole model" caught by J1,
jargon caught by D5/J5/D3. Open rejection_log.md: what failed, why, what changed. Show attempt 2 passing.
**15:00-17:00 Memory + self-evolving.** Open memory/memory.json: learned_rules, check_stats. Run `feedback "..."`, rerun, show rule in prompt.
**17:00-18:00 Trade-offs/limits (face).** Honest limits from README; what you'd build next.
