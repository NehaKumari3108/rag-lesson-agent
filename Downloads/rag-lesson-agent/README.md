# Self-Evaluating Lesson Content Generator (LangGraph)

Generates a beginner lesson, **judges it against a hard pass/fail rubric**, and **regenerates until it clears the bar**
(max 2 retries, so it always terminates). Topic for submission: **Introduction to RAG**.

```
            +-------------+     +----------+     +----------+  all 10 pass   +----------+   +--------+
 topic ---> | load_memory | --> | generate | --> | evaluate | -------------> | finalize | ->| evolve |-> END
            +-------------+     +----------+     +----+-----+                +----------+   +--------+
              learned rules                           | any FAIL, retries left      ^        update memory,
              + human feedback                        v                             |        learn new rules
                                                 +---------+  (reasons fed back)    |
                                                 | rewrite | -> evaluate            |
                                                 +---------+   retries used up ------+  => NEEDS_HUMAN_REVIEW
```

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add ANTHROPIC_API_KEY (or set LLM_PROVIDER=openai / ollama)
export PYTHONPATH=src

python -m lesson_agent run                      # normal run
python -m lesson_agent run --inject-error       # DEMO: plants a false claim + jargon in draft 1
python -m lesson_agent feedback "Use more Indian everyday examples"   # human feedback -> memory
pytest -q                                       # offline tests (LLM_PROVIDER=mock)
```
Ollama (free, local): `LLM_PROVIDER=ollama GEN_MODEL=llama3.1:8b JUDGE_MODEL=llama3.1:8b`.

## Outputs (`outputs/<topic>/`)
| file | what |
|---|---|
| `lesson.md` | the passing lesson (only written if ALL checks pass) |
| `lesson.NEEDS_REVIEW.md` | written instead if retries run out; never shipped as final |
| `rejection_log.md/.json` | per rejected draft: failed checks, reason, evidence quote, what changed on retry |
| `final_scorecard.json` | PASS/FAIL for each of the 10 checks on the final draft |

## The rubric (`src/lesson_agent/data/rubric.yaml`): 10 hard checks, no partial credit
| id | dimension | how checked |
|---|---|---|
| D1 | coherent flow | headings: What / Why / How / Example / Recap (Python) |
| D2 | beginner language | avg sentence <= 15 words, max <= 28 (Python) |
| D3 | no unexplained jargon | every watched term defined where first used (Python) |
| D4 | covers key points | 500-1100 words (Python) |
| D5 | beginner language | no buzzwords / expert phrases, few very long words (Python) |
| J1 | accurate & grounded | no claim contradicts the reference-facts sheet (LLM judge) |
| J2 | covers key points | what / why / how / limits present (LLM judge) |
| J3 | teaches by example | analogy AND worked example (LLM judge) |
| J4 | coherent flow | no concept used before explained (LLM judge) |
| J5 | audience fit | 12th-grade, non-English-medium learner can follow (LLM judge) |

## Self-evolving + memory
`memory/memory.json` persists across runs: run history, per-check fail rates, **learned generator rules** (distilled
from each failure by a reflection step, capped at 8), and human feedback (last 5). All are injected into the next
generation prompt. Checks that fail often (>=3 times, >=40%) are **flagged for a human to review**; the rubric itself is
never auto-edited (see DESIGN.md for why).

## Honest limitations
- `LLM_PROVIDER=mock` is a scripted stand-in for tests; it proves the loop logic, not lesson quality.
- Deterministic jargon check is a heuristic (definition cue words); the LLM judge covers what it misses.
- The judge can still be wrong. Humans should spot-check passed lessons; feedback flows back via `feedback`.
