# agentic-self-correction — plan + evidence

Supporting material for the self-correction improvement of the agentic LLM-in-loop engine.
Start with the summary: [`../agentic-self-correction.md`](../agentic-self-correction.md).

## Contents

- **`improvement-plan.md`** — the guiding plan (LLM-loop improvement brief): what the agentic
  executor is, the self-correction gap vs the already-strong self-maintenance, the controlled
  diagnostic design, the Tier-1/2/3 items (#1 stagnation, #2 ambiguous-vs-absent, #3 wide
  observe, #4a/#4b verify), and the G1–G5 validation methodology. Moved here from its
  authoring location.
- **`results-log.tsv`** — the autoresearch keep/discard ledger, one row per iteration
  (baseline → #3a → #4b → #2+#4a+#1 → sealed) with the real before/after numbers.

The controlled diagnostic set itself lives with the eval harness it runs through
(`eval/eval_set/diagnostic.yaml` + `eval/passk_diag.py`), not here, so it stays runnable.
