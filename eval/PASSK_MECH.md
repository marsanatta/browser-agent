# Reference-mechanism pass^k report — baseline (k=3)

- probes: 6 | overall pass^k: 3/6 | false-success: 0
- TOTAL Copilot calls: 289 | $0.97

## Per family (cost is first-class: calls / in_tok / nano_aiu)

| family | n | pass^k | false-succ | avg calls | avg steps | avg in_tok | avg nano_aiu |
|---|---|---|---|---|---|---|---|
| A | 4 | 1/4 | 0/4 | 21.1 | 19.8 | 182592 | 6.74e9 |
| B | 2 | 2/2 | 0/2 | 6.0 | 5.0 | 39544 | 2.77e9 |

## Per probe

- mech_A_dup_action: pass^k=N false_succ=N calls=26 steps=25 in_tok=229268 [A/same_name_dup_action]
- mech_A_list_edit: pass^k=N false_succ=N calls=25 steps=24 in_tok=231846 [A/same_name_list_pick]
- mech_A_dup_diff_href: pass^k=N false_succ=N calls=28 steps=26 in_tok=235197 [A/same_name_diff_href]
- mech_A_same_dest_control: pass^k=Y false_succ=N calls=5 steps=4 in_tok=34059 [A/same_dest_control]
- mech_B_hidden_nav_coverage: pass^k=Y false_succ=N calls=7 steps=6 in_tok=47087 [B/largedom_hidden_nav_coverage]
- mech_B_control_match: pass^k=Y false_succ=N calls=5 steps=4 in_tok=32002 [B/largedom_control_match]
