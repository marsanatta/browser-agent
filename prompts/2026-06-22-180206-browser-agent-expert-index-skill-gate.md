# Build browser-agent-expert Index Skill And Gate-Test It

- **Datetime:** 2026-06-22 18:02:06
- **Summary:** Replace the flat references.md with a brain-style layered docs index plus a `browser-agent-expert` retrieval skill, then validate routing with an agent-teams loop gate until all questions land on the right reference.

## Prompt

> stop this task.  read /brain skill and create a similar skill with /skill-writer to create a index structure for the docs folder called browser-agent-expert create this skill under .claude/skills in this repo. after you finish spawn /agent-teams you assign each a question and they try this skill. to test if they can correctly find the corresponding reference. this will replace the original references.md this is loop gate process, you assign question, they use skill to find it and give feedback, you refine the index, until pass the gate. /save-prompt

## What I Did

- Stopped the running REFERENCES.md compilation subagent (superseded by this index-skill approach).
- Read the `/brain` skill to model its L0/L1/L2 layered hierarchy (L0 abstract = scan, L1 overview = navigate, L2 = full content) and skill-as-engine / files-as-index separation.
- Rebuilt `docs/INDEX.md` as the layered index: L0 abstract + a keyword **routing table** (topic → exact L2 doc) + per-doc "read it when" + cross-list notes for the two trap topics (milestone eval lives in architecture/07; security split by phase across infra 04/05).
- Authored `.claude/skills/browser-agent-expert/SKILL.md` (skill-writer format): a query engine that reads INDEX, routes, opens the L2 doc, and answers **with citation + verification flag**; plus a maintenance section. Skill carries no hard-coded file list — it trusts INDEX.
- Removed `docs/REFERENCES.md` (replaced by skill + index; per-doc Sources sections remain the L2 bibliography).
- Ran an agent-teams fan-out **loop gate**: 8 fresh subagents, one question each, covering all 8 docs incl. 2 cross-list traps (milestone metric, security). Each used only the skill+INDEX to navigate and reported landing doc + routing friction. Result: 8/8 correct routing (confidence 97–99).
- Refined INDEX from the validated feedback: reworded the security cross-list note (phase-based 04 vs 05), added sample-size keywords to the eval-methodology row, onboarding/overview to the synthesis row, captured-session keywords to the infra row.
- Re-tested the identified weak spot (security-first phrasing) with 1 more subagent → correctly routed to infra/05 (97), confirming the reworded note works. **Gate passed: 9/9.**
