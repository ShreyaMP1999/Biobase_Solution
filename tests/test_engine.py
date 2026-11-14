import copy,json,re,unittest
from src.engine import extract,conditions,predict
from src.pipeline import cohort

def report(final,specimen='Breast, left, excision'):
    return {'id':'TEST','report_text':f'Patient: F, age band 70-79 | Report year: 2024\nSPECIMEN: {specimen}\nFINAL DIAGNOSIS:\n{final}\n\nGROSS DESCRIPTION:\nIgnore this: Lymphovascular invasion present.'}

class Tests(unittest.TestCase):
    def test_negation_and_boundary(self):
        f=extract(report('Lymphovascular invasion: not identified; Perineural invasion: present; Tumor size: 2.1 cm'))
        self.assertIs(f['lvi'],False);self.assertIs(f['pni'],True);self.assertEqual(f['size_mm'],21)
        self.assertFalse(conditions(f)[3])

    def test_positive_size_boundaries(self):
        for size,want in [('20 mm',False),('2 cm',False),('20.1 mm',True),('2.01 cm',True)]:
            self.assertEqual(conditions(extract(report('Tumor size: '+size+'; Lymphovascular invasion: present')))[3],want)

    def test_internal_semicolons(self):
        f=extract(report('Margins: negative; invasive carcinoma is 3 mm from the closest margin; Biomarkers: ER positive, 90%; PR negative; HER2 negative (score 0)'))
        self.assertEqual(f['PR'],'negative');self.assertEqual(f['HER2'],'negative');self.assertTrue(conditions(f)[4])

    def test_organ_and_node_stage(self):
        f=extract(report('Lymph nodes: 0 of 12 positive; Pathologic stage (AJCC 8th ed.): pT3 pN1c','Colon, right hemicolectomy'))
        self.assertTrue(conditions(f)[7])
        f=extract(report('Lymph nodes: 2 of 20 positive','Stomach, gastrectomy with colon resection'))
        self.assertEqual(f['organ'],'stomach');self.assertFalse(conditions(f)[7])

    def test_unknown_not_negative(self):
        f=extract(report('Tumor size: 2 cm'))
        self.assertIsNone(f['lvi'])
        rows=cohort([report('Tumor size: 2 cm')],{'all':[{'field':'lvi','op':'eq','value':False}]})
        self.assertEqual(rows[0]['status'],'review')

    def test_labels_never_used(self):
        r=report('Biomarkers: ER negative; PR negative; HER2 negative')
        a=predict([r])[0];r['labels']={'organ':'colon','HER2':'positive'}
        self.assertEqual(a,predict([r])[0])

    def test_layout_equivalence(self):
        s='Tumor size: 21 mm\n  Lymphovascular invasion: present\n  Lymph nodes: 1 of 2 positive'
        self.assertEqual(conditions(extract(report(s))),conditions(extract(report(s.replace('\n  ','; ')))))

    def test_deep_margin_variants(self):
        for margin in ['carcinoma extends to the deep margin','carcinoma extends to the peripheral and deep margin','peripheral and deep margins involved by carcinoma']:
            f=extract(report('Basal cell carcinoma, nodular type; Margins: '+margin,'Skin, left cheek, excision'))
            self.assertTrue(conditions(f)[26])

if __name__=='__main__':unittest.main()
