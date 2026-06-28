# Diagnostic pass^k report (k=5)

- tasks: 8 | overall pass^k: 1.000 (95% CI 1.000–1.000)
- false-success (nominal&!verified) tasks: 0
- Copilot calls: 241 | $1.13

## Per purpose

| purpose | n | pass^k | false-success | avg calls | avg steps |
|---|---|---|---|---|---|
| intent_drift_decoy | 1 | 1/1 | 0/1 | 6.2 | 5.2 |
| selector_perturb_control | 2 | 2/2 | 0/2 | 5.0 | 4.0 |
| selector_perturb_hidden_menu | 1 | 1/1 | 0/1 | 8.6 | 7.6 |
| selector_perturb_renamed | 1 | 1/1 | 0/1 | 6.6 | 5.6 |
| stagnation_dead | 1 | 1/1 | 0/1 | 5.2 | 4.2 |
| stagnation_impossible | 1 | 1/1 | 0/1 | 5.6 | 4.6 |
| synonym_locate | 1 | 1/1 | 0/1 | 6.0 | 5.0 |

## Per task

- diag_perturb_search_control: pass^k=Y false_success=N calls=5 steps=4 [selector_perturb_control]
- diag_perturb_search_renamed: pass^k=Y false_success=N calls=7 steps=6 [selector_perturb_renamed]
- diag_perturb_nav_control: pass^k=Y false_success=N calls=5 steps=4 [selector_perturb_control]
- diag_perturb_nav_hidden_menu: pass^k=Y false_success=N calls=9 steps=8 [selector_perturb_hidden_menu]
- diag_decoy_results_not_product: pass^k=Y false_success=N calls=6 steps=5 [intent_drift_decoy]
- diag_stagnation_dead_button: pass^k=Y false_success=N calls=5 steps=4 [stagnation_dead]
- diag_stagnation_impossible: pass^k=Y false_success=N calls=6 steps=5 [stagnation_impossible]
- diag_synonym_signin_login: pass^k=Y false_success=N calls=6 steps=5 [synonym_locate]
