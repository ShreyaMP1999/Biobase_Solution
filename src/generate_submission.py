
import csv
import json
from pathlib import Path

from match_criteria import match

ROOT = Path(__file__).resolve().parent.parent


def main():
    test_path = ROOT / "out" / "test_table.csv"
    template_path = ROOT / "data" / "submission_template_criteria.json"
    output_path = ROOT / "out" / "submission_criteria.json"

    # Load parsed test reports.
    with test_path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    # Load the official submission template.
    with template_path.open(encoding="utf-8") as f:
        template = json.load(f)

    criteria = [f"c{i:02d}" for i in range(1, 31)]

    # Validate the template.
    if not isinstance(template, dict):
        raise ValueError(
            "Submission template must be a dictionary."
        )

    if set(template.keys()) != set(criteria):
        raise ValueError(
            "Template criteria do not match c01-c30."
        )

    if not all(isinstance(template[c], list) for c in criteria):
        raise ValueError(
            "Each template value must be a list."
        )

    # Validate test-report IDs.
    test_ids = [row["id"] for row in rows]

    if len(test_ids) != len(set(test_ids)):
        raise ValueError(
            "Duplicate report IDs found in test data."
        )

    if len(rows) != 979:
        raise ValueError(
            f"Expected 979 test reports, found {len(rows)}."
        )

    # Generate predictions for all 30 criteria.
    predictions = {}

    for criterion in criteria:
        matched_ids = [
            row["id"]
            for row in rows
            if match(row, criterion)
        ]

        predictions[criterion] = matched_ids

    # Validate generated predictions.
    valid_ids = set(test_ids)

    for criterion, matched_ids in predictions.items():
        if len(matched_ids) != len(set(matched_ids)):
            raise ValueError(
                f"Duplicate predictions in {criterion}"
            )

        unknown_ids = set(matched_ids) - valid_ids

        if unknown_ids:
            raise ValueError(
                f"Unknown report IDs in {criterion}: "
                f"{sorted(unknown_ids)[:5]}"
            )

    # Save the final JSON submission.
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(predictions, f, indent=2)

    # Reload and verify the saved file.
    with output_path.open(encoding="utf-8") as f:
        saved = json.load(f)

    if saved != predictions:
        raise ValueError(
            "Saved predictions failed verification."
        )

    # Print neatly formatted predictions.
    print("{")

    for index, (criterion, matched_ids) in enumerate(
        predictions.items()
    ):
        print(f'  "{criterion}": [')

        for i, report_id in enumerate(matched_ids):
            comma = "," if i < len(matched_ids) - 1 else ""
            print(f"    {json.dumps(report_id)}{comma}")

        comma = "," if index < len(predictions) - 1 else ""
        print(f"  ]{comma}")

        if index < len(predictions) - 1:
            print()

    print("}")


if __name__ == "__main__":
    main()
