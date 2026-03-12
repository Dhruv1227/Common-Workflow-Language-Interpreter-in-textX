
import argparse
import json
from pathlib import Path
from leadflow_common import LeadFlowConfig, run_training


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--train', required=True)
    ap.add_argument('--id-col', required=True)
    ap.add_argument('--target-col', required=True)
    ap.add_argument('--numeric', required=True)
    ap.add_argument('--categorical', required=True)
    ap.add_argument('--algorithm', required=True)
    ap.add_argument('--test-size', type=float, required=True)
    ap.add_argument('--random-state', type=int, required=True)
    ap.add_argument('--threshold', type=float, required=True)
    ap.add_argument('--cv-folds', type=int, required=True)
    ap.add_argument('--model-out', required=True)
    ap.add_argument('--report-out', required=True)
    args = ap.parse_args()

    cfg = LeadFlowConfig(
        project='cwl-training', description='', train_path=args.train, score_path='data/new_sales_cases.csv',
        id_col=args.id_col, target_col=args.target_col,
        numeric_features=[x for x in args.numeric.split(',') if x],
        categorical_features=[x for x in args.categorical.split(',') if x],
        algorithm=args.algorithm, test_size=args.test_size, random_state=args.random_state,
        threshold=args.threshold, cv_folds=args.cv_folds,
        metrics=['accuracy', 'precision', 'recall', 'f1', 'roc_auc'],
        model_file=args.model_out, predictions_file='outputs/tmp_predictions.csv', report_file=args.report_out
    )
    report = run_training(cfg, '.')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
