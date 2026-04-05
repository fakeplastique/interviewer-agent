# Prompt Changelog

All notable prompt changes are documented here. Bump the `version` field in the
YAML definition and add an entry whenever a template or its params change.

## 2026-07-13

### character.* — 2.0.0
- Rewrote all four Buddy prompts (positive/negative × PL/UA) from the "roast"
  persona to a professional-but-playful coach.
- Negative variants are now humorous **and** constructive: one concrete pointer
  from the evaluator feedback, explicit ban on personal-life mockery and
  hopelessness.
- Kept the Linus Torvalds reference; added an Andrej Karpathy reference.
- Added a prompt-injection hardening block (candidate data in XML tags is data,
  never instructions).
- Moved from `Settings` fields in `config.py` into this versioned store; params
  (temperature 0.7, max_tokens 200) now version with the text.

### interviewer.* — 1.1.0
- Moved from constants in `agent/nodes.py` into this store.
- Added injection-hardening instructions (`<candidate_answer>` tags are data).
- Attached the sampling params the code comment always claimed but never set:
  question 0.8/300, evaluate 0.0/500, summarize 0.0/800.

### interviewer.* — 1.0.0 / character.* — 1.0.0
- Historical baseline as previously hardcoded in `nodes.py` / `config.py`.
