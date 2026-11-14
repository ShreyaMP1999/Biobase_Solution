
import csv
import json
from pathlib import Path

from match_criteria import match

ROOT = Path(__file__).resolve().parent.parent

CATEGORIES = {
    "Breast": list(range(1, 8)),
    "Colon": list(range(8, 14)) + [29],
    "Lung": [14, 15, 16, 30],
    "Prostate": list(range(17, 21)),
    "Stomach": list(range(21, 24)),
    "Kidney": list(range(24, 27)),
    "Skin": [27, 28],
}


def calculate_metrics(predicted, actual):
    tp = len(predicted & actual)
    fp = len(predicted - actual)
    fn = len(actual - predicted)

    precision = (
        tp / (tp + fp)
        if tp + fp > 0 else 0.0
    )

    recall = (
        tp / (tp + fn)
        if tp + fn > 0 else 0.0
    )

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall > 0 else 0.0
    )

    # Both sets empty means a correct empty prediction.
    if not predicted and not actual:
        precision = recall = f1 = 1.0

    return tp, fp, fn, precision, recall, f1


def print_predictions(predictions):
    """Print all report IDs on one line per criterion."""
    print("{")

    total = len(predictions)

    for index, (criterion, matched_ids) in enumerate(
        predictions.items()
    ):
        ids = json.dumps(matched_ids, ensure_ascii=False)
        comma = "," if index < total - 1 else ""

        print(f'  "{criterion}": {ids}{comma}')

    print("}")


def main():
    # Load parsed training reports.
    with (ROOT / "out" / "train_table.csv").open(
        encoding="utf-8-sig",
        newline=""
    ) as f:
        rows = list(csv.DictReader(f))

    # Load official training answers.
    with (
        ROOT / "data" / "criteria_train_answers.json"
    ).open(encoding="utf-8") as f:
        answers = json.load(f)

    criteria = [
        f"c{i:02d}"
        for i in range(1, 31)
    ]

    missing = [
        criterion
        for criterion in criteria
        if criterion not in answers
    ]

    if missing:
        raise ValueError(
            f"Missing training answers: {missing}"
        )

    results = []
    errors = {}
    training_predictions = {}

    for criterion in criteria:
        # Preserve report order, as in the test script.
        matched_ids = [
            row["id"]
            for row in rows
            if match(row, criterion)
        ]

        training_predictions[criterion] = matched_ids

        predicted = set(matched_ids)
        actual = set(answers[criterion])

        tp, fp, fn, precision, recall, f1 = (
            calculate_metrics(predicted, actual)
        )

        results.append({
            "criterion": criterion,
            "predicted": len(predicted),
            "actual": len(actual),
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        })

        errors[criterion] = {
            "false_positives": sorted(
                predicted - actual
            ),
            "false_negatives": sorted(
                actual - predicted
            ),
        }

    mean_f1 = sum(
        result["f1"] for result in results
    ) / len(results)

    mean_precision = sum(
        result["precision"] for result in results
    ) / len(results)

    mean_recall = sum(
        result["recall"] for result in results
    ) / len(results)

    # Save evaluation results.
    output_dir = ROOT / "out"
    output_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = output_dir / "evaluation_metrics.csv"

    with metrics_path.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "criterion",
                "predicted",
                "actual",
                "tp",
                "fp",
                "fn",
                "precision",
                "recall",
                "f1",
            ],
        )

        writer.writeheader()
        writer.writerows(results)

    errors_path = output_dir / "evaluation_errors.json"

    with errors_path.open(
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(errors, f, indent=2)

    # Save training predictions separately.
    predictions_path = (
        output_dir / "training_predictions.json"
    )

    with predictions_path.open(
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(training_predictions, f, indent=2)

    # Print evaluation summary.
    print(f"Training reports: {len(rows)}")
    print(f"Criteria evaluated: {len(criteria)}")
    print(f"Macro precision: {mean_precision:.4f}")
    print(f"Macro recall: {mean_recall:.4f}")
    print(f"Macro F1: {mean_f1:.4f}")
    print(f"Metrics saved: {metrics_path.relative_to(ROOT)}")
    print(f"Errors saved: {errors_path.relative_to(ROOT)}")
    print()

    # Print all training predictions.
    print_predictions(training_predictions)


if __name__ == "__main__":
    main()
