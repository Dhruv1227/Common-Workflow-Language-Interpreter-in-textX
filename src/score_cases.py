
import argparse
from leadflow_common import LeadFlowConfig, run_scoring


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--score', required=True)
    ap.add_argument('--id-col', required=True)
    ap.add_argument('--numeric', required=True)
    ap.add_argument('--categorical', required=True)
    ap.add_argument('--threshold', type=float, required=True)
    ap.add_argument('--model-in', required=True)
    ap.add_argument('--predictions-out', required=True)
    args = ap.parse_args()

    cfg = LeadFlowConfig(
        project='cwl-scoring', description='', train_path='data/train_sales_cases.csv', score_path=args.score,
        id_col=args.id_col, target_col='qualified',
        numeric_features=[x for x in args.numeric.split(',') if x],
        categorical_features=[x for x in args.categorical.split(',') if x],
        algorithm='logistic_regression', test_size=0.2, random_state=42,
        threshold=args.threshold, cv_folds=5,
        metrics=['accuracy'], model_file=args.model_in, predictions_file=args.predictions_out,
        report_file='outputs/tmp_report.json'
    )
    df = run_scoring(cfg, '.')
    print(df.head().to_string(index=False))


if __name__ == '__main__':
    main()
