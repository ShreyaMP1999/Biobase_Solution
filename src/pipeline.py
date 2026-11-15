"""CLI: predict, evaluate, or run an explainable custom cohort search."""
import argparse, csv, hashlib, html, json, statistics, time
from pathlib import Path
from .engine import extract, predict

def load(path):
    with open(path,encoding='utf-8') as f: return json.load(f)

def reports(path):
    with open(path,encoding='utf-8') as f: rows=[json.loads(l) for l in f if l.strip()]
    ids=[r['id'] for r in rows]
    if len(ids)!=len(set(ids)): raise ValueError('Duplicate report IDs')
    for r in rows:
        if not isinstance(r.get('report_text'),str): raise ValueError('Missing report_text')
    if not rows: raise ValueError('No reports found')
    return rows

def save(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(value,indent=2),encoding='utf-8')

def split(r): return 'validation' if int(hashlib.sha256(r['id'].encode()).hexdigest(),16)%5==0 else 'development'

def evaluate(pred,gold,ids):
    result=[]
    for k in gold:
        g=set(gold[k]) & ids; p=set(pred.get(k,[])) & ids
        tp=len(g&p); fp=len(p-g); fn=len(g-p)
        result.append({'criterion':k,'precision':tp/len(p) if p else 0.0,
          'recall':tp/len(g) if g else 0.0,'f1':2*tp/(len(p)+len(g)) if p or g else 0.0,
          'tp':tp,'fp':fp,'fn':fn,'predicted_count':len(p),'true_count':len(g),
          'relative_count_error':abs(len(p)-len(g))/len(g) if g else None,
          'false_positive_ids':sorted(p-g),'false_negative_ids':sorted(g-p)})
    return {'mean_f1':statistics.mean(r['f1'] for r in result),'criteria':result}

def baseline(rs,criteria):
    from .baseline_keyword import words,stem
    texts=[(r['id'],{stem(w) for w in __import__('re').findall(r'[a-z0-9]+',r['report_text'].lower())}) for r in rs]
    return {c['id']:[rid for rid,toks in texts if {stem(w) for w in words(c['text'])}<=toks] for c in criteria}

OPS={'eq':lambda a,b:a==b,'ne':lambda a,b:a!=b,'gt':lambda a,b:a>b,
     'ge':lambda a,b:a>=b,'lt':lambda a,b:a<b,'le':lambda a,b:a<=b,
     'contains':lambda a,b:str(b).lower() in str(a).lower(),'in':lambda a,b:a in b}

def cohort(rs,query):
    rules=query['all']
    if not rules: raise ValueError('At least one rule is required')
    available=set(extract({'report_text':"Patient: F, age band 70-79 | Report year: 2024\nSPECIMEN: Breast\nFINAL DIAGNOSIS: Tumor size: 2 cm\n\nGROSS DESCRIPTION:"}))-{'fields','diagnosis_block','_row'}
    numeric={'age_min','year','size_mm','nodes_positive','closest_margin_mm','nottingham','isup','grade_group'}
    boolean={'lvi','pni','margin_negative','margin_positive','multifocal','bronchial_margin','deep_margin','pleural','svi','epe','sarcomatoid','deposits'}
    for r in rules:
        if r['field'] not in available or r['op'] not in OPS: raise ValueError('Unknown field or operator: '+str(r))
        value=r['value'];values=value if r['op']=='in' else [value]
        if r['op']=='in' and not isinstance(value,list):raise ValueError('The in operator requires a list')
        if r['field'] in numeric:
            if r['op']=='contains' or any(type(v) not in (int,float) for v in values):raise ValueError('Numeric fields require numeric values')
        elif r['field'] in boolean:
            if r['op'] not in ('eq','ne','in') or any(type(v) is not bool for v in values):raise ValueError('Boolean fields require true or false with eq, ne, or in')
        elif r['op'] not in ('eq','ne','contains','in') or any(not isinstance(v,str) for v in values):raise ValueError('Text fields require string values with eq, ne, contains, or in')
    rows=[]
    for report in rs:
        f=extract(report); checks=[]
        for rule in rules:
            value=f.get(rule['field'])
            verdict=None if value is None else bool(OPS[rule['op']](value,rule['value']))
            checks.append({**rule,'observed':value,'status':'unknown' if verdict is None else 'pass' if verdict else 'fail'})
        state='excluded' if any(c['status']=='fail' for c in checks) else 'review' if any(c['status']=='unknown' for c in checks) else 'match'
        rows.append({'id':report['id'],'status':state,'passed':sum(c['status']=='pass' for c in checks),
                     'checks':checks,'evidence':f['diagnosis_block'],'header':report['report_text'].split('FINAL DIAGNOSIS:')[0]})
    return sorted(rows,key=lambda r:({'match':0,'review':1,'excluded':2}[r['status']],-r['passed'],r['id']))

def cohort_html(rows,path,title):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    counts={k:sum(r['status']==k for r in rows) for k in ['match','review','excluded']}
    body=[]
    for r in rows:
        checks=''.join('<li>'+html.escape(f"{c['field']} {c['op']} {c['value']}: {c['observed']} ({c['status']})")+'</li>' for c in r['checks'])
        body.append('<details data-status="'+r['status']+'"><summary>'+html.escape(r['id']+' | '+r['status'])+'</summary><ul>'+checks+'</ul><pre>'+html.escape(r['header']+r['evidence'])+'</pre></details>')
    Path(path).write_text('<!doctype html><meta charset="utf-8"><title>Cohort Explorer</title><style>body{font:16px system-ui;max-width:1000px;margin:40px auto;background:#f6f8fc;color:#17233a}details{background:white;padding:14px;margin:10px 0;border-radius:9px}pre{white-space:pre-wrap}select,input{padding:10px;margin:10px}</style><h1>'+html.escape(title)+'</h1><p>'+html.escape(str(counts))+'</p><p>Unknown means missing evidence. Review and excluded reports are not matches.</p><select id="filter"><option value="all">All reports</option><option>match</option><option>review</option><option>excluded</option></select><input id="search" placeholder="Search ID or evidence"><div>'+''.join(body)+'</div><script>const filter=document.getElementById("filter");const search=document.getElementById("search");function update(){document.querySelectorAll("details").forEach(d=>d.hidden=!(filter.value==="all"||d.dataset.status===filter.value)||!d.textContent.toLowerCase().includes(search.value.toLowerCase()))}filter.onchange=update;search.oninput=update;</script>',encoding='utf-8')

def main(argv=None):
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='command',required=True)
    for name in ['predict','evaluate','cohort']:
        p=sub.add_parser(name);p.add_argument('--reports',required=True)
        p.add_argument('--out',default='submissions/submission_criteria.json' if name=='predict' else None,required=name!='predict')
        if name in ['predict','evaluate']:p.add_argument('--criteria',default='data/criteria.json')
        if name=='predict':
            p.add_argument('--template',help='Optional official submission template to validate')
            p.add_argument('--audit-out',help='Audit JSON path (default: out/<submission stem>.audit.json)')
        if name=='evaluate':
            p.add_argument('--answers',required=True);p.add_argument('--split',choices=['all','development','validation'],default='validation')
        if name=='cohort':p.add_argument('--query',required=True)
    a=ap.parse_args(argv);rs=reports(a.reports);t=time.perf_counter()
    if a.command=='cohort':
        query=load(a.query);rows=cohort(rs,query);save(a.out,rows)
        cohort_html(rows,str(Path(a.out).with_suffix('.html')),query.get('name','Cohort Explorer'))
        print({k:sum(r['status']==k for r in rows) for k in ['match','review','excluded']});return
    criteria=load(a.criteria)
    from .validation import validate_criteria
    validate_criteria(criteria)
    if a.command=='evaluate' and a.split!='all':rs=[r for r in rs if split(r)==a.split]
    if not rs: raise ValueError('Selected split contains no reports')
    if a.command=='predict' and a.template:
        from .validation import validate_template
        validate_template(load(a.template))
    pred,audit=predict(rs)
    if a.command=='predict':
        from .validation import validate_submission
        validate_submission(pred,{r['id'] for r in rs})
        audit_path=Path(a.audit_out) if a.audit_out else Path('out')/(Path(a.out).stem+'.audit.json')
        if audit_path.resolve()==Path(a.out).resolve():
            raise ValueError('Submission and audit paths must be different')
        save(a.out,pred);save(audit_path,audit)
        print('Submission:',a.out);print('Audit:',audit_path)
        print('Wrote all 30 criteria; matching IDs:',sum(map(len,pred.values())))
    else:
        gold=load(a.answers);ids={r['id'] for r in rs}
        if set(gold)!=set(pred):raise ValueError('Answer key must cover all 30 criteria')
        result={'split':a.split,'reports':len(rs),'rule_system':evaluate(pred,gold,ids),'keyword_baseline':evaluate(baseline(rs,criteria),gold,ids)}
        save(a.out,result)
        with Path(a.out).with_suffix('.metrics.csv').open('w',newline='',encoding='utf-8') as f:
            fields=['criterion','precision','recall','f1','tp','fp','fn','predicted_count','true_count','relative_count_error']
            writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(result['rule_system']['criteria'])
        print('Reports:',len(rs),'Rule mean F1:',round(result['rule_system']['mean_f1'],6),'Baseline:',round(result['keyword_baseline']['mean_f1'],6))
    print('Seconds:',round(time.perf_counter()-t,3))

if __name__=='__main__':main()

