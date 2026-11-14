"""Parse synthetic pathology reports into one flat table row per report.

Usage:
    python3 parse_reports.py data/train.jsonl out/train_table.csv
    python3 parse_reports.py data/test.jsonl  out/test_table.csv

Works on both FINAL DIAGNOSIS layouts (one field per line, or all fields on one
line joined by "; "). Values such as Margins and Biomarkers contain ";" too, so
we only split where the next piece starts with a KNOWN field name + ":".
Also derives typed columns (sizes in mm, node counts, ER/PR/HER2, Gleason, ...)
that the criterion filters use.
"""
import csv, json, re, sys

# Every field name listed in the README, across all organs.
FIELDS = """Specimen; Diagnosis; Margins; Tumor size; Aggressive growth pattern; Ulceration;
Perineural invasion; Depth; Pathologic stage; Depth of invasion; Lymphovascular invasion;
High-risk features; Pathologic stage (AJCC 8th ed.); Invasive carcinoma; Breslow thickness;
Mitotic rate; Regression; Tumor-infiltrating lymphocytes; Microscopic satellites; Neurotropism;
Extension along follicular epithelium; Dermal invasion; Residual melanoma in this excision;
Biopsy correlation; Part B, sentinel lymph nodes (left inguinal); Part B, sentinel lymph nodes (left axillary);
Clark level; Part B, sentinel lymph nodes (right inguinal); Part B, sentinel lymph nodes (left cervical);
Part B, sentinel lymph nodes (right axillary); Part B, sentinel lymph nodes (right cervical);
Tumor site; Histologic type; Nottingham grade; Tumor focality; Ductal carcinoma in situ; Lymph nodes;
Biomarkers; Neoadjuvant therapy; Visceral pleural invasion; Gleason score; Tumor extent; Cribriform glands;
Intraductal carcinoma; Extraprostatic extension; Seminal vesicle invasion; Histologic grade; HER2;
Macroscopic tumor perforation; Tumor deposits; ISUP grade; Sarcomatoid or rhabdoid features; Extent of invasion"""
FIELDS = [f.strip() for f in FIELDS.replace("\n", " ").split(";") if f.strip()]
# Rejoin "Part B, sentinel ..." names that the naive split above broke on ","? (they use "," not ";", so fine)
# Longest first so "Pathologic stage (AJCC 8th ed.)" wins over "Pathologic stage".
FIELDS.sort(key=len, reverse=True)
FIELD_RE = "|".join(re.escape(f) for f in FIELDS)
STARTS_FIELD = re.compile(rf"^(?:{FIELD_RE}):\s*")
SPLIT_ONELINE = re.compile(rf";\s+(?=(?:{FIELD_RE}):)")

ORGAN_FROM_SPECIMEN = [("lung", "lung"), ("skin", "skin"), ("breast", "breast"), ("prostate", "prostate"),
                       ("stomach", "stomach"), ("colon", "colon"), ("kidney", "kidney")]


def organ_of(specimen):
    # Earliest organ word wins: "Colon ..., en bloc resection of stomach" is colon.
    s = specimen.lower()
    hits = [(s.find(k), organ) for k, organ in ORGAN_FROM_SPECIMEN if k in s]
    return min(hits)[1] if hits else None


def parse_block(block):
    """FINAL DIAGNOSIS text -> {field: value}, plus a 'Diagnosis' for unlabeled lines (skin)."""
    block = block.strip()
    lines = [l.strip() for l in block.split("\n") if l.strip()]
    if len(lines) == 1:  # one-line layout
        text = lines[0]
        if text.endswith("."):
            text = text[:-1]
        pieces = SPLIT_ONELINE.split(text)
    else:
        pieces = lines
    out = {}
    for p in pieces:
        m = STARTS_FIELD.match(p)
        if m:
            name = p[: m.end()].rstrip().rstrip(":").rstrip()
            out[name] = p[m.end():].strip()
        else:  # unlabeled line = the skin diagnosis
            out["Diagnosis"] = (out["Diagnosis"] + "; " + p) if "Diagnosis" in out else p
    return out


def parse_report(text):
    head = re.search(r"Patient:\s*(\w+), age band ([^|]+?)\s*\|\s*Report year:\s*(\d{4})", text)
    spec = re.search(r"SPECIMEN:\s*(.*)", text).group(1).strip()
    fd = re.search(r"FINAL DIAGNOSIS:(.*?)(?:\n\s*\n|GROSS DESCRIPTION:|$)", text, re.S).group(1)
    diag = {"Specimen": spec}
    diag.update(parse_block(fd))
    return {
        "sex": head.group(1), "age_band": head.group(2).strip(), "report_year": int(head.group(3)),
        "organ": organ_of(spec), "diagnosis": diag,
    }


# ---------- typed / derived columns ----------
def size_mm(v):
    if not v:
        return None
    m = re.search(r"(\d+(?:\.\d+)?)\s*(mm|cm)\b", v)
    if not m:
        return None
    x = float(m.group(1))
    return x * 10 if m.group(2) == "cm" else x


def present(v):
    """True / False / None for 'present' vs 'not identified' style fields."""
    if v is None:
        return None
    s = v.lower()
    if re.match(r"\s*(not identified|absent|negative|none|no\b)", s):
        return False
    if re.match(r"\s*(present|identified|positive|yes)", s):
        return True
    return None


def nodes(v):
    if not v:
        return None, None
    m = re.search(r"(\d+)\s+of\s+(\d+)", v)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None


def marker(bio, name):
    """'positive' / 'negative' / 'equivocal' / None for ER, PR, HER2 inside a Biomarkers or HER2 field."""
    if not bio:
        return None
    m = re.search(rf"\b{name}\b\s+(positive|negative|equivocal|low)", bio, re.I)
    return m.group(1).lower() if m else None


def derive(rec):
    d = rec["diagnosis"]
    stage = d.get("Pathologic stage (AJCC 8th ed.)") or d.get("Pathologic stage") or ""
    toks = stage.split()
    pT = next((t for t in toks if re.match(r"y?pT", t)), None)
    pN = next((t for t in toks if re.match(r"y?pN", t)), None)
    if pT and not pN and (rec["organ"] != "skin" or "melanoma" in (d.get("Diagnosis") or "").lower()):
        pN = "pNX"  # labels use pNX when the stage line gives no N category
    npos, nexam = nodes(d.get("Lymph nodes"))
    bio = d.get("Biomarkers") or ""
    gl = re.search(r"(\d)\s*\+\s*(\d)\s*=\s*(\d+)", d.get("Gleason score", ""))
    gg = re.search(r"Grade Group\s*(\d)", d.get("Gleason score", ""), re.I)
    age_lo = re.match(r"(\d+)", rec["age_band"])
    row = {
        "organ": rec["organ"], "sex": rec["sex"], "age_band": rec["age_band"],
        "age_min": int(age_lo.group(1)) if age_lo else None, "report_year": rec["report_year"],
        "stage_text": stage, "pT": pT, "pN": pN,
        "histology": d.get("Histologic type") or d.get("Diagnosis"),
        "tumor_size_mm": size_mm(d.get("Tumor size")),
        "nodes_pos": npos, "nodes_exam": nexam,
        "lvi": present(d.get("Lymphovascular invasion")),
        "pni": present(d.get("Perineural invasion")),
        "er": marker(bio, "ER"), "pr": marker(bio, "PR"),
        "her2": marker(bio, "HER2") or marker(d.get("HER2"), "HER2") or (
            (d.get("HER2") or "").split()[0].lower().strip(",;") if d.get("HER2") else None),
        "gleason_primary": int(gl.group(1)) if gl else None, "gleason_secondary": int(gl.group(2)) if gl else None,
        "grade_group": int(gg.group(1)) if gg else None,
    }
    return row


def load(path):
    out = []
    for line in open(path):
        if line.strip():
            r = json.loads(line)
            rec = parse_report(r["report_text"])
            rec["id"] = r["id"]
            rec["row"] = derive(rec)
            out.append(rec)
    return out


def main(inp, outp):
    recs = load(inp)
    fields = sorted({k for r in recs for k in r["diagnosis"]})
    derived = list(recs[0]["row"].keys())
    with open(outp, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id"] + derived + ["dx:" + k for k in fields])
        for r in recs:
            w.writerow([r["id"]] + [r["row"][k] for k in derived] + [r["diagnosis"].get(k, "") for k in fields])
    print(f"wrote {outp}: {len(recs)} rows, {len(derived)} derived + {len(fields)} raw fields")


if __name__ == "__main__":
    main(*sys.argv[1:3])
