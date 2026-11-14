"""Validate challenge inputs without publishing restricted challenge text."""
import hashlib,json
CRITERIA_DIGEST='f282dd04acaf486d9b9aa6bfd5607f2df205d73033a78dcfa720a9ab65b76d2e'

def validate_criteria(criteria):
    digest=hashlib.sha256(json.dumps(criteria,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if digest!=CRITERIA_DIGEST:
        raise ValueError('Rules implement the supplied 30 criteria only; changed criteria require changed rules.')

def validate_template(template):
    keys={f'c{i:02d}' for i in range(1,31)}
    if not isinstance(template,dict) or set(template)!=keys or not all(isinstance(v,list) for v in template.values()):
        raise ValueError('Template must contain exactly c01-c30 with list values')
