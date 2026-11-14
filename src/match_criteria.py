
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def number(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def positive(value):
    return str(value).strip().lower() == "positive"


def negative(value):
    return str(value).strip().lower() == "negative"


def field(row, name):
    return str(row.get(name, "") or "").strip().lower()


def has(row, name, phrase):
    return phrase in field(row, name)


def is_true(row, name):
    return field(row, name) == "true"


def is_false(row, name):
    return field(row, name) == "false"


def match(row, criterion):
    organ = field(row, "organ")
    histology = field(row, "histology")

    nodes = number(row.get("nodes_pos"))
    size = number(row.get("tumor_size_mm"))
    grade_group = number(row.get("grade_group"))

    er = field(row, "er")
    pr = field(row, "pr")
    her2 = field(row, "her2")
    lvi = field(row, "lvi")
    pni = field(row, "pni")
    pt = field(row, "pT")

    margins = field(row, "dx:Margins")
    focality = field(row, "dx:Tumor focality")
    grade = field(row, "dx:Nottingham grade")
    age_band = field(row, "age_band")

    # ==========================================
    # BREAST CANCER: c01-c07
    # ==========================================

    if criterion == "c01":
        return (
            organ == "breast"
            and negative(her2)
            and nodes is not None
            and nodes >= 1
        )

    if criterion == "c02":
        return (
            organ == "breast"
            and positive(er)
            and negative(pr)
        )

    if criterion == "c03":
        return (
            organ == "breast"
            and negative(er)
            and negative(pr)
            and negative(her2)
        )

    if criterion == "c04":
        return (
            organ == "breast"
            and lvi == "true"
            and size is not None
            and size > 20
        )

    if criterion == "c05":
        if organ != "breast" or not margins.startswith("negative"):
            return False

        m = re.search(
            r"invasive carcinoma is\s+([\d.]+)\s*mm",
            margins
        )

        return bool(m and float(m.group(1)) <= 3)

    if criterion == "c06":
        return (
            organ == "breast"
            and focality.startswith("multifocal")
            and age_band in {
                "0-17", "18-29", "30-39",
                "40-49", "50-59"
            }
        )

    if criterion == "c07":
        return (
            organ == "breast"
            and bool(re.search(r"^3\b", grade))
            and lvi == "false"
        )

    # ==========================================
    # COLON CANCER: c08-c13
    # ==========================================

    
    if criterion == "c08":
        return (
            organ == "colon"
            and (
                (nodes is not None and nodes >= 1)
                or field(row, "pN") == "pn1c"
            )
        )


    if criterion == "c09":
        return (
            organ == "colon"
            and histology == "mucinous adenocarcinoma"
        )

    if criterion == "c10":
        return (
            organ == "colon"
            and has(row, "dx:Tumor deposits", "present")
            and not has(row, "dx:Tumor deposits", "not present")
        )

    if criterion == "c11":
        return (
            organ == "colon"
            and nodes == 0
            and lvi == "true"
        )

    if criterion == "c12":
        return (
            organ == "colon"
            and pt.startswith("pt4")
        )

    if criterion == "c13":
        return (
            organ == "colon"
            and size is not None
            and size >= 50
            and pni == "false"
        )

    # ==========================================
    # LUNG CANCER: c14-c16
    # ==========================================

    # FIXED: Values include "present (PL1)" and
    # "present (PL2)", not just "present".
    if criterion == "c14":
        invasion = field(row, "dx:Visceral pleural invasion")
        return (
            organ == "lung"
            and invasion.startswith("present")
        )

    if criterion == "c15":
        return (
            organ == "lung"
            and "squamous cell carcinoma" in histology
            and "bronchial" in margins
            and (
                "involved" in margins
                or "positive" in margins
            )
        )

    if criterion == "c16":
        return (
            organ == "lung"
            and "adenocarcinoma" in histology
            and nodes is not None
            and nodes >= 1
        )

    # ==========================================
    # PROSTATE CANCER: c17-c20
    # ==========================================

    if criterion == "c17":
        return (
            organ == "prostate"
            and grade_group is not None
            and grade_group >= 4
        )

    # FIXED: Values include "present, left",
    # "present, right", and "present, bilateral".
    if criterion == "c18":
        invasion = field(row, "dx:Seminal vesicle invasion")
        return (
            organ == "prostate"
            and invasion.startswith("present")
        )

    # FIXED: Extraprostatic extension uses
    # "not identified (organ-confined)".
    if criterion == "c19":
        extension = field(row, "dx:Extraprostatic extension")
        return (
            organ == "prostate"
            and margins.startswith("positive")
            and extension.startswith("not identified")
        )

    if criterion == "c20":
        return (
            organ == "prostate"
            and pni == "true"
            and lvi == "false"
        )

    # ==========================================
    # STOMACH CANCER: c21-c23
    # ==========================================

    if criterion == "c21":
        return (
            organ == "stomach"
            and positive(her2)
        )

    if criterion == "c22":
        return (
            organ == "stomach"
            and "poorly cohesive" in histology
            and "diffuse" in histology
            and "mixed" not in histology
            and nodes is not None
            and nodes >= 1
        )

    if criterion == "c23":
        return (
            organ == "stomach"
            and pt.startswith("pt4")
        )

    # ==========================================
    # KIDNEY CANCER: c24-c26
    # ==========================================

    if criterion == "c24":
        isup = field(row, "dx:ISUP grade")
        return (
            organ == "kidney"
            and "clear cell renal cell carcinoma" in histology
            and bool(re.search(r"\b[34]\b", isup))
        )

    if criterion == "c25":
        features = field(
            row, "dx:Sarcomatoid or rhabdoid features"
        )
        return (
            organ == "kidney"
            and "present" in features
            and "not present" not in features
        )

    # FIXED: The parser uses "dx:Extent of invasion".
    if criterion == "c26":
        extent = field(row, "dx:Extent of invasion")
        return (
            organ == "kidney"
            and (
                "renal vein" in extent
                or "inferior vena cava" in extent
            )
        )

    # ==========================================
    # SKIN CANCER: c27-c28
    # ==========================================

    # FIXED: Require carcinoma specifically
    # involving or extending to the deep margin.
    if criterion == "c27":
        return (
            organ == "skin"
            and "basal cell carcinoma" in histology
            and (
                "carcinoma extends to the deep margin" in margins
                or "carcinoma extends to the peripheral and deep margin" in margins
                or "deep margin involved by carcinoma" in margins
                or "peripheral and deep margins involved by carcinoma" in margins
            )
        )

    if criterion == "c28":
        return (
            organ == "skin"
            and "invasive squamous cell carcinoma" in histology
            and (
                "moderately differentiated" in histology
                or "poorly differentiated" in histology
                or "(g2)" in histology
                or "(g3)" in histology
            )
        )

    # ==========================================
    # ADDITIONAL CRITERIA: c29-c30
    # ==========================================

    if criterion == "c29":
        return (
            organ == "colon"
            and age_band in {
                "70-79", "80-89", "90-99", "100+"
            }
            and nodes is not None
            and nodes >= 1
        )

    if criterion == "c30":
        return (
            organ == "lung"
            and field(row, "sex") == "f"
            and field(row, "report_year") in {"2023", "2024"}
        )

    return False


def main():
    path = ROOT / "out" / "train_table.csv"

    with path.open(
        encoding="utf-8-sig",
        newline=""
    ) as f:
        rows = list(csv.DictReader(f))

    criteria = [
        f"c{i:02d}"
        for i in range(1, 31)
    ]

    print("=" * 50)
    print("ELIGIBILITY LENS - ALL 30 CRITERIA")
    print("=" * 50)
    print(f"Total reports loaded: {len(rows)}")
    print("-" * 50)

    for criterion in criteria:
        matches = [
            row["id"]
            for row in rows
            if match(row, criterion)
        ]

        print(f"{criterion}: {len(matches)} matches")

    print("-" * 50)
    print("All 30 criteria processed.")


if __name__ == "__main__":
    main()
