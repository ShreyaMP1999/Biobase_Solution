"""Compatibility entry point for the unified predict command."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if __package__:
    from .pipeline import main as pipeline_main
else:
    sys.path.insert(0,str(ROOT))
    from src.pipeline import main as pipeline_main

def main():
    pipeline_main(['predict'] + ['--reports',str(ROOT/'data/test.jsonl'),'--criteria',str(ROOT/'data/criteria.json'),'--out',str(ROOT/'out/submission_criteria.json')] + sys.argv[1:])

if __name__ == "__main__":
    main()
