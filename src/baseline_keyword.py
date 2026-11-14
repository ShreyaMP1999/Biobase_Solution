"""Reference baseline: plain keyword search. No field parsing, no numbers, no negation.
A report matches a criterion when it contains every content word of the criterion
(or a simple stem of it). Usage:
    python3 baseline_keyword.py test.jsonl criteria.json submission.json
Beat this score and you have shown the work does more than keyword search."""
import json, re, sys

STOP = set("a an and any are as at be by cancer cancers carcinoma for from has have in is it of on or patient patients that the to under with within without no not more than larger smaller older aged female male".split())
ALIAS = {"hers": "her2", "her2": "her2"}

def words(s):
    out = []
    for w in re.findall(r"[a-z0-9]+", s.lower()):
        if w in STOP or w.isdigit(): continue
        out.append(w)
    return out

def stem(w):
    return w[:6] if len(w) > 6 else w

def main(test_path, criteria_path, out_path):
    crit = json.load(open(criteria_path))
    reports = [json.loads(l) for l in open(test_path)]
    texts = [(r["id"], set(stem(w) for w in re.findall(r"[a-z0-9]+", r["report_text"].lower()))) for r in reports]
    sub = {}
    for c in crit:
        need = set(stem(w) for w in words(c["text"]))
        sub[c["id"]] = [rid for rid, toks in texts if need <= toks]
    json.dump(sub, open(out_path, "w"))
    print("wrote", out_path, {k: len(v) for k, v in list(sub.items())[:5]}, "...")

if __name__ == "__main__":
    main(*sys.argv[1:4])
