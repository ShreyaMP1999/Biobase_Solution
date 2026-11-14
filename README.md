
# Eligibility Lens

A rule-based patient eligibility matching system developed for the Biobase "Find the Right Patients" challenge at the DNAForge AI x Biology Hackathon, Berkeley, November 2026.

## Overview

Eligibility Lens identifies pathology reports that satisfy clinical eligibility criteria.

The system extracts structured information from synthetic pathology reports and applies predefined matching rules to identify eligible patient records.

## Dataset

The challenge provides synthetic pathology reports in JSONL format.

- Training reports: 9,010
- Test reports: 979
- Eligibility criteria: 30

The dataset includes information such as cancer type, histology, tumor size, lymph node involvement, pathological stage, biomarkers, and surgical margins.

The source data is excluded from this repository in accordance with the challenge's data-access restrictions.

## Methodology

The system follows four steps:

1. Parse pathology reports and extract relevant clinical information.
2. Convert extracted information into structured records.
3. Apply rule-based eligibility criteria to each record.
4. Generate matching report IDs for each criterion.

The matching engine handles clinical details such as biomarker status, tumor measurements, lymph node involvement, pathological staging, and negation.

## Project Structure

```text
Eligibility-lens/
├── data/                 # Challenge data (not tracked)
├── out/                  # Generated outputs (not tracked)
├── src/
│   ├── baseline_keyword.py
│   ├── check_parser.py
│   ├── evaluate.py
│   ├── field_values.py
│   ├── generate_submission.py
│   ├── match_criteria.py
│   ├── parse_reports.py
│   └── score.py
├── tests/
├── .gitignore
├── README.md
├── README_parser.md
└── requirements.txt
```

## Evaluation

The matching engine was evaluated against the provided training answer key.

| Metric | Training Result |
|--------|-----------------|
| Precision (macro) | 1.0000 |
| Recall (macro) | 1.0000 |
| F1 Score (macro) | 1.0000 |

All 30 criteria matched the provided training labels after rule refinement.

These results represent agreement with the training answers and should not be interpreted as independent test-set performance.

## Test Predictions

The finalized matching engine was applied to 979 held-out pathology reports.

- Reports processed: 979
- Criteria evaluated: 30
- Criterion-report matches generated: 608

The predictions are stored in `out/submission_criteria.json`.

The held-out F1 score requires evaluation against the official test answer key.

## Running the Project

Install dependencies:

```bash
pip install -r requirements.txt
```

Generate the structured report tables using the parser, then evaluate the training predictions:

```bash
python src/evaluate.py
```

Generate test predictions:

```bash
python src/generate_submission.py
```

## Output Format

The submission is a JSON object mapping each criterion ID to the matching pathology report IDs.

Example:

```json
{
  "c01": ["SYN-example001"],
  "c02": ["SYN-example002"],
  "c03": []
}
```

The IDs above are illustrative.

## Limitations

- The system implements 30 predefined eligibility rules.
- It does not automatically interpret arbitrary new natural-language criteria.
- Training performance may not reflect performance on unseen reports.
- The dataset is synthetic and is not clinically validated.
- The system is a research prototype, not a clinical decision-making tool.

## Team

Team T15 — DNAForge AI x Biology Hackathon

- Vaishnavi Kosuru
- Tia RaoRane
- Shreya Padaganur

## Acknowledgments

Biobase and the DNAForge AI x Biology Hackathon organizers for providing the challenge and research environment.
