---
name: browser-agent-expert
description: "Answer browser-automation-agent design questions by routing through the docs/ knowledge base and citing the exact source. Use when asked how to build/evaluate/deploy the browser agent, which reference covers a topic, or any architecture/eval/infra question for this repo. Replaces a flat references list with a layered, navigable index."
argument-hint: "[your question about the browser agent]"
---

# browser-agent-expert

The retrieval engine over this repo's grounding research in `docs/`. Given a question about building, evaluating, or shipping the browser-automation agent, it navigates a layered index (brain-style L0→L1→L2) and returns a grounded answer **with the exact source citation** — instead of forcing the reader to scan a flat bibliography.

The skill is the engine; the data lives in [docs/INDEX.md](../../../docs/INDEX.md) (L1 routing) and the `docs/research/**` documents (L2). Keep logic here, keep facts there.

## When to Use

- Someone asks an architecture / evaluation / infrastructure question about the browser agent ("how should the agent perceive the page?", "how do I detect silent failures?", "self-host Playwright or Browserbase?").
- Someone asks "which doc / reference covers X" or "where do we say Y".
- Before designing or implementing a component — pull the grounded decision and its source first.
- Verifying a claim: find the authoritative source and its verification status.

## The index (what you navigate)

| Layer | Where | Use for |
|---|---|---|
| **L0** | the one-line `*L0:*` abstract on each doc row in `docs/INDEX.md` | fast scan / filter |
| **L1** | the **routing table** + "read it when" lists in `docs/INDEX.md` | route a question to the right doc |
| **L2** | `docs/research/**/*.md` and their `Sources` sections | the full content + authoritative bibliography |

## Query protocol

1. **Read `docs/INDEX.md`.** Always start here — it is the routing layer and may have changed.
2. **Route.** Match the question's keywords to a row in the routing table. Pick the single best doc; if the question genuinely spans categories, pick all that apply (and consider `research/00-synthesis...` as the cross-category fallback).
3. **Open the L2 doc(s).** Read the relevant section. For a specific claim or number, also read that doc's `Sources` section to get the primary URL and any verification flag.
4. **Answer** in this shape:
   - **Answer:** the grounded finding (1–4 sentences).
   - **Source:** `docs/research/<category>/<file>.md` → primary URL(s) if a specific external source backs it.
   - **Confidence/caveat:** surface any inline flag — `vendor-unverified`, future-dated arXiv ID, or "open problem" — do not present a flagged claim as settled.
5. **No match?** Say so plainly, name the closest doc, and suggest the question may need new research rather than guessing.

Never answer a docs-covered question from memory — route and cite. If you didn't open the doc, say "I haven't verified against the docs."

## Examples

```
Q: "Should the agent read the DOM, the accessibility tree, or use vision?"
→ INDEX routing row "perception … DOM vs accessibility tree, vision" → architecture/01
→ Answer: hybrid DOM+AX indexed list is the convergent choice; vision/SoM only when
  DOM grounding is ambiguous and only with sparse, precise boxes.
→ Source: docs/research/architecture/01-sota-browser-agents.md (§2 perception).
```

```
Q: "How do I know the agent didn't just claim success?"
→ routing rows "silent-failure detection" (evaluation/03) + "verifying without ground
  truth" (evaluation/06)
→ Answer: dual-channel — programmatic state check + screenshot-grounded judge scored
  twice; report nominal vs verified completion (CuP); never trust verbalized confidence.
→ Source: evaluation/03 (§4) and evaluation/06 (silent-failure layer).
```

```
Q: "Is tree search worth it for our agent?"
→ routing row "tree search, LATS, MCTS" → architecture/07
→ Answer: skip it — ~17× token cost and needs transaction-safe state reversion;
  linear retry-with-reflection gives +29% at ~3× instead.
→ Source: docs/research/architecture/07-memory-search-and-milestone-eval.md.
→ Caveat: LATS web results are WebShop-only (flagged in the doc).
```

## Maintenance (keep the index in sync)

When research docs are added, moved, or removed:
1. Add/update a **routing row** and an **L0 line** in `docs/INDEX.md` for the new doc.
2. Verify every routing target path resolves to a real file.
3. If a doc changes category folder, update both `docs/INDEX.md` and any link in `research/00-synthesis...`.

The skill carries no hard-coded file list on purpose — it trusts `docs/INDEX.md`. A stale index is the only way this skill misroutes, so the index is the thing to fix.

## Tips

- Route first, read second — don't open all 8 docs; the routing table exists so you open 1–2.
- The synthesis (`research/00-...`) is the right target only for "big picture / where do I start", not for a specific mechanism — those live in the category docs.
- Watch the cross-list traps: milestone/deterministic eval is in `architecture/07` (not evaluation/); security is split across `infrastructure/04` and `infrastructure/05`.
- Always carry the verification flag through to the answer — a `vendor-unverified` 99.97% is not a fact.
- If two questions keep landing on the wrong doc, the fix is a better keyword in the `docs/INDEX.md` routing row, not more logic in this skill.
