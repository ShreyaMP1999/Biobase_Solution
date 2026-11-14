"""Check parse_reports.py against train labels: every diagnosis field, plus organ/sex/age/year/pT/pN.
Usage: python3 check_parser.py data/train.jsonl"""
import json, sys, collections
from parse_reports import parse_report, derive

errs = collections.Counter(); examples = {}
n = 0
for line in open(sys.argv[1]):
    r = json.loads(line); lab = r["labels"]; n += 1
    rec = parse_report(r["report_text"]); row = derive(rec)
    got, want = rec["diagnosis"], lab["diagnosis"]
    for k in set(got) | set(want):
        if got.get(k) != want.get(k):
            errs["dx:" + k] += 1; examples.setdefault("dx:" + k, (r["id"], got.get(k), want.get(k)))
    for k, gv in [("organ", rec["organ"]), ("sex", rec["sex"]), ("age_band", rec["age_band"]),
                  ("report_year", rec["report_year"]), ("pT", row["pT"]), ("pN", row["pN"])]:
        if gv != lab[k]:
            errs[k] += 1; examples.setdefault(k, (r["id"], gv, lab[k]))
print(f"{n} reports checked")
if not errs:
    print("ALL FIELDS MATCH LABELS EXACTLY")
for k, c in errs.most_common():
    print(f"  {k}: {c} mismatches  e.g. {examples[k]}")
