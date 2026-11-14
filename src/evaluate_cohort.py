"""Evaluate a custom query against an intersection of known training criteria."""
import argparse
from .pipeline import reports,load,save,split,cohort,evaluate

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reports',default='data/train.jsonl')
    parser.add_argument('--answers',default='data/criteria_train_answers.json')
    parser.add_argument('--query',default='validated_query.json')
    parser.add_argument('--criteria-ids',nargs='+',default=['c01','c04'])
    parser.add_argument('--split',choices=['all','development','validation'],default='validation')
    parser.add_argument('--out',default='out/custom_validation.json')
    args=parser.parse_args()
    rows=reports(args.reports)
    if args.split!='all':rows=[r for r in rows if split(r)==args.split]
    if not rows:raise ValueError('Selected split contains no reports')
    answers=load(args.answers)
    if any(c not in answers for c in args.criteria_ids):raise ValueError('Unknown answer criterion')
    expected=set.intersection(*(set(answers[c]) for c in args.criteria_ids))
    results=cohort(rows,load(args.query))
    predicted=[r['id'] for r in results if r['status']=='match']
    metrics=evaluate({'custom':predicted},{'custom':list(expected)},{r['id'] for r in rows})
    output={'split':args.split,'reports':len(rows),'reference_intersection':args.criteria_ids,**metrics}
    save(args.out,output)
    print('Custom cohort F1:',metrics['mean_f1'])

if __name__=='__main__':main()
