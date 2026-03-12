
import argparse
import json
from pathlib import Path
import pandas as pd
from leadflow_common import LeadFlowConfig, validate_config


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--train', required=True)
    ap.add_argument('--score', required=True)
    ap.add_argument('--id-col', required=True)
    ap.add_argument('--target-col', required=True)
    ap.add_argument('--numeric', required=True)
    ap.add_argument('--categorical', required=True)
    ap.add_argument('--out', default='outputs/validation_report.json')
    args = ap.parse_args()

    cfg = LeadFlowConfig(
        project='validation-only', description='', train_path=args.train, score_path=args.score,
        id_col=args.id_col, target_col=args.target_col,
        numeric_features=[x for x in args.numeric.split(',') if x],
        categorical_features=[x for x in args.categorical.split(',') if x],
        algorithm='logistic_regression', test_size=0.2, random_state=42, threshold=0.5, cv_folds=5,
        metrics=['accuracy'], model_file='artifacts/tmp.joblib', predictions_file='outputs/tmp.csv', report_file='outputs/tmp.json'
    )
    train_df = pd.read_csv(args.train)
    score_df = pd.read_csv(args.score)
    report = validate_config(cfg, train_df, score_df)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
