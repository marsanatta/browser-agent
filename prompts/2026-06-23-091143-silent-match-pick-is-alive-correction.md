# Correction: the silent _match wrong-pick is ALIVE (and harness scores it as CuP)

- **Datetime:** 2026-06-23 09:11:43
- **Summary:** User caught an over-correction. Re-ran the two _match paths I had skipped (substring different-name; same-name distinct-href) and proved the silent wrong-pick IS real and the harness DOES turn it into a CuP event.

## Prompt

> i read the _match and locate code myself and i think you over corrected ... target 'log' on
> a page with 'Login Page' 'Login' 'Blog login' returns candidates[0]='Login Page', a uniquely
> named wrong element, so locate tier 1 role+name exact resolves it at count==1 and clicks it
> silently ... even the same name case goes silent when the two elements have different href or
> id, like two 'Read more' links ... run the deterministic test again on the case your last test
> missed ... is the silent _match pick really dead like you said, or alive on the path you didn't
> test /save-prompt

## What I Did

- Ran two deterministic data-URL + MockPlanner scenarios through the REAL Executor:
  - A: substring target 'log' over ['Login Page','Login','Blog login'] -> _match candidates[0]='Login Page' -> locate tier1 role_name (count==1) -> clicked L1 (WRONG) -> nominal=True, verified=False -> CuP silent wrong-pick = TRUE.
  - B: two 'Read more' links with distinct href -> _match candidates[0]=first -> locate tier7 href (count==1) -> clicked A1 (WRONG) -> nominal=True, verified=False -> CuP silent wrong-pick = TRUE.
- CONCEDED: my prior "silent pick is dead" was an over-correction from one unrepresentative test (identical name AND no distinguishing attr -> locate falls through all tiers -> loud NOT_FOUND). The silent pick is ALIVE whenever candidates[0] is uniquely resolvable (unique name via substring, or shared name + distinct href/id).
- Corrected the tasks.yaml comment to state: silent wrong-pick is proven real and harness-catchable; the identical-"(about)" task is a loud red, not the silent demonstrator; a proper silent-pick task must use the substring or same-name-distinct-attr structure.
- Straight answer: the harness CAN turn a silent wrong-pick into a CuP event -> growing the task set WILL catch it, provided adversarial tasks use the silent structure (not identical-name-no-attr).
