# Design decisions and trade-offs

1. **Hybrid evaluator (5 Python + 5 LLM checks).** Anything measurable (length, sentence length, headings, buzzwords,
   jargon-definition) is plain code: free, instant, identical every run. LLMs are used only for judgement
   (accuracy, example quality, flow, audience fit). Trade-off: heuristics can be crude; the LLM layer backs them up.
2. **Hard pass/fail, fail-closed.** The task asks for no partial credit. A missing or garbled judge verdict counts as FAIL,
   and the judge is told to FAIL when unsure. Cost: some false rejections, which is cheaper than shipping bad content.
3. **Grounding sheet for accuracy.** The judge compares the lesson to a short human-written facts file instead of trusting
   its own memory. This makes "accurate" checkable. Trade-off: someone must write the sheet per topic (`--facts`).
4. **Separate judge model.** Judge defaults to a different/stronger model than the generator to reduce self-preference bias.
   The judge is told to ignore instructions inside the lesson (prompt-injection guard).
5. **Targeted rewrite, not regeneration from scratch.** Retry receives the failed checks + evidence quotes + fix hints and
   must make the smallest edits and list what changed. This keeps passed parts stable and gives a real "what changed" log
   (also checked with a line diff).
6. **Guaranteed termination.** `max_retries` (default 2). When exhausted: status NEEDS_HUMAN_REVIEW and the file is named
   `lesson.NEEDS_REVIEW.md`, so unverified content can never look final.
7. **Self-evolution is bounded and safe.** Failures -> reflection -> short imperative rules (max 8) added to the generator
   prompt. The **rubric is not auto-edited**: letting the system loosen its own judge is how quality silently drifts.
   Frequent failures are flagged for a human instead. Generator sees the rubric in plain words (it should know the bar);
   independence comes from the judge's separate model + reference facts.
8. **Memory** = JSON file (simple, diffable, no infra). Swap for SQLite/vector store if it grows.
9. **LangGraph** because the flow is a real cycle with a conditional edge and shared state; n8n would hide the logic
   I want to show, and a plain `while` loop gives no trace/graph view.
10. **Next steps:** per-topic fact sheets from retrieved sources, A/B test learned rules, calibrate the judge against
    human labels, add a Hinglish/Hindi gloss option for key terms.
