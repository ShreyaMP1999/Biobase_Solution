import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.pipeline import main
from src.validation import validate_submission


class SubmissionTests(unittest.TestCase):
    def test_default_folder_and_official_format(self):
        with tempfile.TemporaryDirectory() as folder:
            previous = Path.cwd()
            try:
                os.chdir(folder)
                Path('reports.jsonl').write_text(json.dumps({
                    'id': 'FIXTURE-001',
                    'report_text': 'Patient: F, age band 70-79 | Report year: 2024\nSPECIMEN: Breast\nFINAL DIAGNOSIS:\nBiomarkers: ER positive; PR negative; HER2 negative\n\nGROSS DESCRIPTION:'
                }) + '\n')
                Path('criteria.json').write_text('[]')
                with patch('src.validation.validate_criteria'):
                    main(['predict', '--reports', 'reports.jsonl', '--criteria', 'criteria.json'])
                output = Path('submissions/submission_criteria.json')
                submission = json.loads(output.read_text())
                validate_submission(submission, {'FIXTURE-001'})
                self.assertEqual(list(submission), [f'c{i:02d}' for i in range(1, 31)])
                self.assertEqual(submission['c02'], ['FIXTURE-001'])
                self.assertEqual(submission['c03'], [])
                self.assertEqual(list(Path('submissions').iterdir()), [output])
                self.assertTrue(Path('out/submission_criteria.audit.json').exists())
                with patch('src.validation.validate_criteria'):
                    with self.assertRaisesRegex(ValueError, 'paths must be different'):
                        main(['predict', '--reports', 'reports.jsonl', '--criteria', 'criteria.json',
                              '--out', 'same.json', '--audit-out', 'same.json'])
                self.assertFalse(Path('same.json').exists())
            finally:
                os.chdir(previous)

    def test_invalid_submission_rejected(self):
        for invalid in [['UNKNOWN'], ['A', 'A'], [12], {'count': 1}]:
            submission = {f'c{i:02d}': [] for i in range(1, 31)}
            submission['c01'] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_submission(submission, {'A'})


if __name__ == '__main__':
    unittest.main()
