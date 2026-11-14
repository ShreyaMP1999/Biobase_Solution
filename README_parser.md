# Eligibility Lens — parser, scorer, baseline (Vaishnavi)

Put the challenge files in `data/` (train.jsonl, test.jsonl, criteria.json, criteria_train_answers.json).

| Command | What it does |
|---|---|
| `python3 parse_reports.py data/test.jsonl out/test_table.csv` | Report → one row per patient. Handles both FINAL DIAGNOSIS layouts. |
| `python3 check_parser.py data/train.jsonl` | Checks the parser against train labels. Current result: all 9,010 match exactly (every diagnosis field + organ, sex, age band, year, pT, pN). |
| `python3 score.py sub.json data/criteria_train_answers.json data/criteria.json` | Per-criterion P / R / F1 and mean F1 (skipped = 0, same as the challenge). |
| `python3 field_values.py data/train.jsonl` | Writes `out/field_values.md`: every distinct value pattern per organ and field, for writing filters. |

In Python: `from parse_reports import load; recs = load("data/test.jsonl")` gives each report's `id`, `diagnosis` dict (raw fields) and `row` (typed: tumor_size_mm, nodes_pos/nodes_exam, lvi, pni, er/pr/her2, gleason, grade_group, pT, pN, age_min, sex, year).

Keyword baseline on train: mean F1 0.285, 23/30 answered (README says 0.27 on test).
Pattern: recall ≈ 1 but precision is low, because it ignores negation ("not identified"), numbers (20 mm, age 70) and which field a word sits in. Seven criteria get 0 because their wording (e.g. "triple-negative", "stage III", "pT4") never appears in the reports.

Notes: labels use `pNX` (not null) when the stage line has no N category; skin SCC that is staged has pN null.
