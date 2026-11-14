# Parser and scorer reference

Run commands from the repository root. Obtain the challenge files separately in `data/`; data and generated results are ignored by Git.

| Command | Purpose |
|---|---|
| `python3 src/parse_reports.py data/test.jsonl out/test_table.csv` | Parse raw reports into typed and diagnosis columns; creates the output directory. |
| `python3 src/check_parser.py data/train.jsonl` | Compare parsed diagnosis fields, organ, sex, age band, year, pT, and pN with training labels. |
| `python3 src/field_values.py data/train.jsonl` | Inspect value patterns in `out/field_values.md`. |
| `python3 src/score.py predictions.json answers.json data/criteria.json` | Score an existing prediction file against answers for the same reports. |

Python package import: `from src.parse_reports import load`. Each record contains `id`, `diagnosis` (raw fields), and `row` (typed facts).

The unified `python3 run.py predict` and `python3 run.py evaluate` commands process raw JSONL directly; CSV generation is optional. The shared matcher accepts both native typed values and CSV strings, preserving `False` as an absent finding.

On the supplied training set, the parser matches all 9,010 labels exactly. Labels are used for checking, never for prediction. The keyword baseline mean F1 is 0.284756 on the full training set.

The parser retains pNX when the stage line has no N category, except skin SCC cases that are not node-staged. For full commands, metrics, custom cohort exploration, and limitations, see README.md.
