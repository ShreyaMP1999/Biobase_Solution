"""Shared text-only pipeline using the team's parser and matching rules."""
import re
from .parse_reports import parse_report, derive, present, size_mm
from .match_criteria import match

def find(pattern,text,default=None,cast=str):
    m=re.search(pattern,text,re.I)
    return cast(m.group(1)) if m else default

def extract(report):
    text=report['report_text']
    rec=parse_report(text)
    row=derive(rec)
    d=rec['diagnosis']
    flat={**row,**{'dx:'+k:v for k,v in d.items()}}
    block=find(r'FINAL DIAGNOSIS:\s*([\s\S]*?)(?:\n\s*GROSS DESCRIPTION:|$)',text,'')
    margins=d.get('Margins','').lower()
    negative=bool(re.match('negative',margins)) if margins else None
    positive=bool(re.search(r'\bpositive\b|\binvolved\b|\binvolves\b|carcinoma extends to',margins)) if margins else None
    def margin_status(kind):
        if re.search(r'carcinoma extends to (?:the )?(?:peripheral and )?'+kind+r' margins?|'+kind+r' margins? (?:positive|involved)',margins):return True
        value=find(kind+r' margins?\s+([^;]+)',margins,'')
        return present(value) if value else None
    return {
      'organ':row['organ'],'age_min':row['age_min'],'sex':row['sex'],'year':row['report_year'],
      'histology':(row['histology'] or '').lower(),'size_mm':row['tumor_size_mm'],
      'nodes_positive':row['nodes_pos'],'pT':row['pT'],'pN':row['pN'],
      'ER':row['er'],'PR':row['pr'],'HER2':row['her2'],'lvi':row['lvi'],'pni':row['pni'],
      'margin_negative':negative,'margin_positive':positive,
      'closest_margin_mm':find(r'invasive carcinoma is\s+(\d+(?:\.\d+)?)\s*mm',margins,cast=float),
      'multifocal':d.get('Tumor focality','').lower().startswith('multifocal') if d.get('Tumor focality') else None,
      'nottingham':find(r'([123])',d.get('Nottingham grade',''),cast=int),
      'isup':find(r'([1-4])',d.get('ISUP grade',''),cast=int),'grade_group':row['grade_group'],
      'renal_extent':d.get('Extent of invasion','').lower(),
      'bronchial_margin':margin_status('bronchial'),'deep_margin':margin_status('deep'),
      'pleural':present(d.get('Visceral pleural invasion')),'svi':present(d.get('Seminal vesicle invasion')),
      'epe':present(d.get('Extraprostatic extension')),'sarcomatoid':present(d.get('Sarcomatoid or rhabdoid features')),
      'deposits':present(d.get('Tumor deposits')),'fields':d,'diagnosis_block':block,'_row':flat}

def conditions(features):
    return [match(features['_row'],f'c{i:02d}') for i in range(1,31)]

def predict(reports):
    out={f'c{i:02d}':[] for i in range(1,31)};audit=[]
    for report in reports:
        f=extract(report);matched=[]
        for i,yes in enumerate(conditions(f),1):
            if yes:out[f'c{i:02d}'].append(report['id']);matched.append(f'c{i:02d}')
        public={k:v for k,v in f.items() if k!='_row'}
        audit.append({'id':report['id'],'matched':matched,'features':public})
    return out,audit
