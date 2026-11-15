# Generated submissions

Run `python3 run.py predict --reports data/test.jsonl` from the repository root.
This folder is created automatically and receives `submission_criteria.json`.
Upload that JSON file to the challenge scorer. It contains exactly c01-c30,
each mapped to a list of test report ID strings. Audit evidence is saved
separately in `out/submission_criteria.audit.json`. Generated JSON is ignored
by Git because it contains challenge report IDs.
