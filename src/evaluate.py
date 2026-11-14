"""Compatibility entry point for the unified evaluate command."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if __package__:
    from .pipeline import main as pipeline_main
else:
    sys.path.insert(0,str(ROOT))
    from src.pipeline import main as pipeline_main

def main():
    pipeline_main(['evaluate'] + ['--reports',str(ROOT/'data/train.jsonl'),'--answers',str(ROOT/'data/criteria_train_answers.json'),'--criteria',str(ROOT/'data/criteria.json'),'--split','all','--out',str(ROOT/'out/evaluation.json')] + sys.argv[1:])

if __name__ == "__main__":
    main()
