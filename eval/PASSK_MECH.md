# Reference-mechanism pass^k report — stable_id (k=3)

- probes: 6 | overall pass^k: 5/6 | false-success: 0
- TOTAL Copilot calls: 129 | $0.34

## Per family (cost is first-class: calls / in_tok / nano_aiu)

| family | n | pass^k | false-succ | avg calls | avg steps | avg in_tok | avg nano_aiu |
|---|---|---|---|---|---|---|---|
| A | 4 | 4/4 | 0/4 | 6.7 | 5.7 | 46895 | 1.73e9 |
| B | 2 | 1/2 | 0/2 | 8.2 | 7.2 | 63379 | 2.14e9 |

## Per probe

- mech_A_dup_action: pass^k=Y false_succ=N calls=6 steps=5 in_tok=41558 [A/same_name_dup_action]
- mech_A_list_edit: pass^k=Y false_succ=N calls=7 steps=6 in_tok=47133 [A/same_name_list_pick]
- mech_A_dup_diff_href: pass^k=Y false_succ=N calls=9 steps=8 in_tok=64640 [A/same_name_diff_href]
- mech_A_same_dest_control: pass^k=Y false_succ=N calls=5 steps=4 in_tok=34247 [A/same_dest_control]
- mech_B_hidden_nav_coverage: pass^k=N false_succ=N calls=11 steps=10 in_tok=89983 [B/largedom_hidden_nav_coverage]
- mech_B_control_match: pass^k=Y false_succ=N calls=5 steps=4 in_tok=36774 [B/largedom_control_match]
