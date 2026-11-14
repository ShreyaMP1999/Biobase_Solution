"""List distinct values per (organ, field) in train, with counts -> out/field_values.md.
Long free-text fields are shown as their top values only. Usage: python3 field_values.py data/train.jsonl"""
import sys, collections, re
from parse_reports import load
recs = load(sys.argv[1])
by = collections.defaultdict(collections.Counter)
for r in recs:
    for k, v in r["diagnosis"].items():
        if k == "Specimen": continue
        # collapse numbers so "9 mm" / "12 mm" group together
        by[(r["organ"], k)][re.sub(r"\d+(\.\d+)?", "#", v)] += 1
with open("out/field_values.md", "w") as f:
    f.write("# Distinct field values in train (numbers shown as #)\n")
    for organ in sorted({o for o, _ in by}):
        f.write(f"\n## {organ}\n")
        for (o, k), c in sorted(by.items()):
            if o != organ: continue
            f.write(f"\n**{k}** ({len(c)} patterns)\n")
            for v, n in c.most_common(12):
                f.write(f"- `{v}` — {n}\n")
print("wrote out/field_values.md")
