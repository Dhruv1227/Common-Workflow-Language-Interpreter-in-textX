
import argparse
import json
from pathlib import Path
import pandas as pd
from leadflow_common import parse_leadflow, validate_config, run_training, run_scoring


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--grammar', required=True)
    ap.add_argument('--dsl', required=True)
    ap.add_argument('--root', default='.')
    args = ap.parse_args()

    root = Path(args.root)
    cfg = parse_leadflow(root / args.grammar, root / args.dsl)
    train_df = pd.read_csv(root / cfg.train_path)
    score_df = pd.read_csv(root / cfg.score_path)
    validation = validate_config(cfg, train_df, score_df)
    print('VALIDATION')
    print(json.dumps(validation, indent=2))
    report = run_training(cfg, root)
    print('TRAINING REPORT')
    print(json.dumps(report, indent=2))
    predictions = run_scoring(cfg, root)
    print('TOP PREDICTIONS')
    print(predictions.head().to_string(index=False))


if __name__ == '__main__':
    main()
