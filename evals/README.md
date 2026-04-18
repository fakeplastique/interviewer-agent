# LLM Evaluation Pipeline

Two layers, both reading prompts from the single source of truth
(`backend/app/prompts/definitions/`):

1. **promptfoo** — prompt-quality evals with deterministic asserts + LLM-as-judge
   rubrics (tone, language, constructiveness, prompt-injection resistance).
2. **pytest evals** (`backend/tests/evals/`) — structured-output regression
   against golden answers; catches breakage when bumping `ANTHROPIC_MODEL` or
   `langchain-anthropic`.

Both need `ANTHROPIC_API_KEY` and cost real money — they never run in the
default test suite. CI runs them via `.github/workflows/evals.yml` only when
prompt/eval/LLM-plumbing files change, or on manual dispatch (requires the
`ANTHROPIC_API_KEY` repo secret).

## Running locally

```bash
# promptfoo suites (from the repo root)
npx promptfoo@latest eval -c evals/character_positive.config.yaml
npx promptfoo@latest eval -c evals/character_negative.config.yaml
npx promptfoo@latest eval -c evals/interviewer_question.config.yaml
npx promptfoo@latest view   # browse results

# pytest evals
cd backend && pytest tests/evals -m eval -v
```

## Adding cases

- Prompt-quality cases: add vars (plus optional per-case `assert`) to
  `evals/datasets/*.yaml`.
- Score-band cases: add a `GoldenAnswer` to
  `backend/tests/evals/test_structured_eval.py`.

When you change a prompt, bump its `version` in the YAML definition and record
the change in `backend/app/prompts/CHANGELOG.md`; the eval suites are the
regression gate for that change.
