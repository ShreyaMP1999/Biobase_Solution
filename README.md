# Eligibility Lens

Explainable pathology report search for the Biobase "Find the Right Patients" challenge, DNAForge AI x Biology Hackathon, November 2026.

The project supports **criteria search** and **our own idea: an explainable cohort explorer**. Both use the same report parser and matching pipeline. Slide organ labeling and similar-slide retrieval are not implemented; those require a separate image dataset and pipeline.

## Quick start

Use Python 3.10 or newer. No extra packages, API keys, GPU, or paid model are required.

Clone this repository and run commands from its root. Obtain the authorized challenge files separately and place them under `data/` with these names:

```text
data/
  train.jsonl
  test.jsonl
  criteria.json
  criteria_train_answers.json
  submission_template_criteria.json  # optional
```

Source challenge files and generated report IDs are deliberately excluded from Git. Do not commit them. Input filenames with download suffixes such as `train(2).jsonl` can be passed explicitly with `--reports`, or renamed locally.

### Criteria search

```bash
python3 run.py predict --reports data/test.jsonl --out out/submission_criteria.json
```

This processes raw JSONL directly. A parsed CSV and the optional submission template are not prerequisites. To validate an available template, add `--template data/submission_template_criteria.json`.

Outputs:

- `out/submission_criteria.json`: submit this file for criteria search, containing all 30 criterion IDs and matching test report IDs.
- `out/submission_criteria.audit.json`: extracted facts, matched criteria, and source diagnosis text for review. This is not the submission file.

The system implements the supplied 30 fixed criteria, not arbitrary natural-language rules. The supplied criteria file is validated against a fingerprint to reject unsupported changes without publishing its text here. Training labels are never consulted during prediction.

### Our own idea: explainable cohort explorer

```bash
python3 run.py cohort --reports data/test.jsonl --query example_query.json --out out/cohort.json
```

Open `out/cohort.html` locally in your browser. Search IDs or evidence, filter results, and expand a report to view each condition, its observed value, and source diagnosis text. The page works offline.

The example looks for breast reports with HER2 negative, at least one positive lymph node, and tumor size greater than 20 mm. It finds 5 exact matches in the supplied test set.

| Status | Meaning |
|---|---|
| Match | All filters pass |
| Review | No filter fails, but one or more required facts are missing |
| Excluded | At least one filter fails |

Edit `example_query.json` to create a different cohort. Its `all` array combines conditions with AND. Supported operators are `eq`, `ne`, `gt`, `ge`, `lt`, `le`, `contains`, and `in`. Operators and values must match the field type. Missing information never counts as a negative finding or an exact match. Sorting by passed filters is not an eligibility probability.

Useful fields: `organ`, `age_min`, `sex`, `year`, `histology`, `size_mm`, `nodes_positive`, `pT`, `pN`, `ER`, `PR`, `HER2`, `lvi`, `pni`, `nottingham`, `isup`, `grade_group`, `multifocal`, `pleural`, `svi`, `epe`, `sarcomatoid`, `deposits`, and margin fields. See `src/engine.py` for the complete schema. `age_min` is a band lower bound, not an exact age; use band-aligned filters such as >=70 or <60. Text equality is case-sensitive; organ and histology values are lowercase and marker values are `positive`, `negative`, or `equivocal`.

## Evaluation

```bash
python3 run.py evaluate --reports data/train.jsonl --answers data/criteria_train_answers.json --split all --out out/full_train.json
python3 run.py evaluate --reports data/train.jsonl --answers data/criteria_train_answers.json --split validation --out out/validation.json
python3 -m src.evaluate_cohort
```

Evaluation saves a JSON summary, per-criterion precision/recall/F1, error IDs, count errors, and a metrics CSV. It also runs the supplied keyword baseline on the same reports. The cohort evaluation compares `validated_query.json` with the intersection of c01 and c04 training answers, which represents the same AND condition. For another query, the reference criteria must represent that query exactly.

Measured on the supplied data after integration:

| Evaluation | Reports | Rule mean F1 | Keyword mean F1 |
|---|---:|---:|---:|
| Full training set | 9,010 | 1.000000 | 0.284756 |
| Internal validation subset | 1,811 | 1.000000 | 0.259695 |

The custom cohort also scores F1 1.0 on the internal validation subset. Test predictions process 979 reports and contain 608 criterion/report matches, exactly matching the earlier solution. **Test F1 remains unknown until compared with the official test answers.**

The internal split uses SHA256(report ID) modulo 5: zero selects validation, the rest selects development. IDs determine only the split and output, never clinical features. These fixed rules were refined against supplied training data, including your collaborator's full-training work, so this split is not an independent blind evaluation of the combined project. Both subsets share a synthetic generator.

F1 per criterion is `2 * TP / (2 * TP + FP + FN)`. The headline score averages all 30 criteria. A skipped or count-only criterion gets zero F1. The local scorer uses zero when both ID sets are empty; this convention does not affect the reported evaluations, where all 30 criteria have positives. Count error is undefined when the true count is zero and is saved as null.

## Implementation

- `src/parse_reports.py`: the team's shared parser for both final diagnosis layouts, typed sizes, node counts, biomarkers, and demographics.
- `src/match_criteria.py`: the team's 30 explicit matching rules.
- `src/engine.py`: connects parsed facts to matching rules and cohort features, with audit evidence.
- `src/pipeline.py`: unified prediction, evaluation, and cohort commands.
- `src/generate_submission.py`, `src/evaluate.py`: compatibility commands; now process raw JSONL automatically.
- `src/evaluate_cohort.py`: evaluates the custom cohort against known training-answer intersections.
- `src/score.py`: scores an existing prediction file, including count-only submissions.
- `tests/`: synthetic regression fixtures that do not need restricted data.
- `.github/workflows/tests.yml`: Python 3.10 and 3.13 CI.

The parser separates known field headings rather than every semicolon, keeps margin/biomarker values intact, normalizes cm to mm, and uses the primary specimen organ. Matching reads final diagnosis facts rather than unrelated measurements in gross prose.

Criterion c08 follows the supplied training answer key's stage III interpretation: colon pN1c is included even with zero positive lymph nodes. Criteria c11 and c29 use the literal positive-node count. The rules also handle 90+ age bands and require bronchial margin involvement specifically for c15.

## Additional commands

```bash
python3 src/generate_submission.py
python3 src/evaluate.py
python3 src/parse_reports.py data/train.jsonl out/train_table.csv
python3 src/parse_reports.py data/test.jsonl out/test_table.csv
python3 src/check_parser.py data/train.jsonl
python3 src/field_values.py data/train.jsonl
python3 src/score.py out/submission_criteria.json path/to/correct_test_answers.json data/criteria.json
python3 -m unittest discover -s tests -v
```

The parser check matches all 9,010 training reports exactly against their structured labels. Those labels are used only for this check. The 18 regression tests cover negatives, missing fields, size boundaries, internal semicolons, mixed layouts, organ selection, 90+ ages, specific margins, preservation of native boolean values, cohort output, HTML escaping, and F1 arithmetic.

## Limitations and next steps

This is a synthetic-data hackathon prototype, not a clinical decision tool. Fixed criteria and custom AND filters do not interpret arbitrary clinical questions. Unseen report formats, complex mixed margins, and unsupported concepts require additional extraction rules and an untouched evaluation set. The reports do not correspond to the challenge slides.

For a future natural-language interface, compile questions into the validated filter schema and reject unsupported concepts. For slide tasks, build a separate image embedding and classification pipeline after obtaining the authorized slide files.

## Team

Team T15: Vaishnavi Kosuru, Tia RaoRane, and Shreya Padaganur.

This combined implementation preserves the team's parser and matching work and integrates the explainable cohort explorer, shared command line, regression tests, and reproducible evaluation. Thanks to Biobase and the DNAForge AI x Biology Hackathon organizers.
