"""Per-criterion precision / recall / F1, same rules as the challenge:
mean F1 over all 30 criteria, a skipped or empty criterion scores 0.

Usage:
    python3 score.py my_submission.json data/criteria_train_answers.json [data/criteria.json]

Accepts any of the README answer forms per criterion: a list of ids,
{"ids": [...], "count": n}, or {"count": n} (count-only earns no F1, but we
report its relative count error).
"""
import json, sys


def ids_of(v):
    if isinstance(v, list):
        return set(v)
    if isinstance(v, dict) and "ids" in v:
        return set(v["ids"])
    return None


def score(sub, gold):
    rows = []
    for cid in sorted(gold):
        g = set(gold[cid])
        v = sub.get(cid)
        p_ids = ids_of(v)
        row = {"id": cid, "gold": len(g), "pred": None, "tp": 0, "P": 0.0, "R": 0.0, "F1": 0.0, "count_err": None}
        if p_ids is not None:
            tp = len(p_ids & g)
            P = tp / len(p_ids) if p_ids else 0.0
            R = tp / len(g) if g else 0.0
            F = 2 * P * R / (P + R) if P + R else 0.0
            row.update(pred=len(p_ids), tp=tp, P=P, R=R, F1=F)
        cnt = v.get("count") if isinstance(v, dict) else (len(v) if isinstance(v, list) else None)
        if cnt is not None and g:
            row["count_err"] = abs(cnt - len(g)) / len(g)
        rows.append(row)
    return rows


def main(sub_path, gold_path, crit_path=None):
    sub, gold = json.load(open(sub_path)), json.load(open(gold_path))
    text = {c["id"]: c["text"] for c in json.load(open(crit_path))} if crit_path else {}
    rows = score(sub, gold)
    print(f"{'id':4} {'gold':>5} {'pred':>5} {'tp':>5} {'P':>5} {'R':>5} {'F1':>5}  criterion")
    for r in rows:
        pred = "-" if r["pred"] is None else r["pred"]
        print(f"{r['id']:4} {r['gold']:5} {pred:>5} {r['tp']:5} {r['P']:5.2f} {r['R']:5.2f} {r['F1']:5.2f}  {text.get(r['id'], '')[:70]}")
    mean = sum(r["F1"] for r in rows) / len(rows)
    answered = sum(1 for r in rows if r["pred"])
    print(f"\nMEAN F1 = {mean:.3f}   answered {answered} of {len(rows)}   perfect (F1=1) {sum(r['F1'] == 1 for r in rows)}")
    return mean


if __name__ == "__main__":
    main(*sys.argv[1:4])
