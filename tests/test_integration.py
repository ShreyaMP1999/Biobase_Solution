"""Small synthetic fixtures keep CI independent of restricted challenge data."""
import json,subprocess,sys,tempfile,unittest
from pathlib import Path
from src.engine import extract,conditions,predict
from src.match_criteria import match,field
from src.pipeline import cohort,evaluate
from src.validation import validate_template,validate_criteria
from src.parse_reports import parse_report,derive,main as parse_main
from src.score import score

ROOT=Path(__file__).resolve().parents[1]

def make_report(final,specimen='Breast, excision',age='90+'):
    return {'id':'FIXTURE-001','report_text':f'Patient: F, age band {age} | Report year: 2024\n\nSPECIMEN: {specimen}\n\nFINAL DIAGNOSIS:\n  {final}\n\nGROSS DESCRIPTION:\nSynthetic fixture.'}

class IntegrationTests(unittest.TestCase):
    def test_false_survives_memory_and_csv(self):
        self.assertEqual(field({'lvi':False},'lvi'),'false')
        for value in [False,'False','false']:
            self.assertTrue(match({'organ':'breast','lvi':value,'dx:Nottingham grade':'3'},'c07'))

    def test_age_90_plus(self):
        f=extract(make_report('Lymph nodes: 1 of 8 positive','Colon, resection'))
        self.assertTrue(conditions(f)[28])

    def test_specific_margin(self):
        row={'organ':'lung','histology':'squamous cell carcinoma','dx:Margins':'bronchial margin negative; vascular margin involved'}
        self.assertFalse(match(row,'c15'))
        row['dx:Margins']='bronchial margin involved; vascular margin negative'
        self.assertTrue(match(row,'c15'))

    def test_mixed_layout_and_colon_biomarkers(self):
        r=make_report('Histologic type: carcinoma; Tumor size: 2 CM\n  Biomarkers: ER: positive; PR: negative; HER2: negative\n  Lymphovascular invasion: not identified')
        f=extract(r)
        self.assertEqual(f['size_mm'],20);self.assertEqual(f['ER'],'positive')
        self.assertEqual(f['PR'],'negative');self.assertEqual(f['HER2'],'negative')

    def test_parser_creates_output_directory(self):
        with tempfile.TemporaryDirectory() as td:
            inp=Path(td)/'input.jsonl';out=Path(td)/'new'/'table.csv'
            inp.write_text(json.dumps(make_report('Tumor size: 2 cm'))+'\n')
            parse_main(inp,out);self.assertTrue(out.exists())

    def test_cohort_cli_and_html_escape(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td);r=make_report('Tumor size: 2.1 cm; Lymphovascular invasion: not identified; Histologic type: <script>bad()</script>')
            (td/'input.jsonl').write_text(json.dumps(r)+'\n')
            (td/'query.json').write_text(json.dumps({'name':'<test>','all':[{'field':'size_mm','op':'gt','value':20}]}))
            output=td/'results'/'cohort.json'
            run=subprocess.run([sys.executable,str(ROOT/'run.py'),'cohort','--reports',str(td/'input.jsonl'),'--query',str(td/'query.json'),'--out',str(output)],cwd=td,capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual(json.loads(output.read_text())[0]['status'],'match')
            page=output.with_suffix('.html').read_text()
            self.assertIn('&lt;script&gt;',page);self.assertNotIn('<script>bad()',page)

    def test_filter_type_validation(self):
        with self.assertRaises(ValueError):cohort([make_report('Tumor size: 2 cm')],{'all':[{'field':'size_mm','op':'gt','value':'20'}]})
        with self.assertRaises(ValueError):cohort([make_report('Tumor size: 2 cm')],{'all':[{'field':'organ','op':'in','value':'breast'}]})

    def test_template_and_criteria_guards(self):
        validate_template({f'c{i:02}':[] for i in range(1,31)})
        with self.assertRaises(ValueError):validate_template({'c01':[]})
        with self.assertRaises(ValueError):validate_criteria([{'id':'c01','text':'new condition'}])

    def test_unsupported_criterion_rejected(self):
        with self.assertRaises(ValueError):match({},'c99')

    def test_score_and_count_only(self):
        row=score({'c01':['A','B','C','E']},{'c01':['A','B','C','D']})[0]
        self.assertEqual(row['F1'],.75)
        row=score({'c01':{'count':4}},{'c01':['A','B','C','D']})[0]
        self.assertEqual(row['F1'],0);self.assertEqual(row['count_err'],0)
        self.assertEqual(evaluate({'c01':['A','B','C','E']},{'c01':['A','B','C','D']},set('ABCDE'))['mean_f1'],.75)

if __name__=='__main__':unittest.main()
