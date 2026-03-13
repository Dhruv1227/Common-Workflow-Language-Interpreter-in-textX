from __future__ import annotations
import argparse
import json
from pathlib import Path
import yaml
from leadflow_common import parse_leadflow
import pandas as pd


# Helper functions for CWL compatibility

def _tool_requirements():
    return {
        'InlineJavascriptRequirement': {},
        'EnvVarRequirement': {
            'envDef': [
                {'envName': 'PYTHONUNBUFFERED', 'envValue': '1'}
            ]
        }
    }


def _as_cli_arguments(items: list[str]):
    return [{'valueFrom': item} for item in items]


def cwl_tool_validate(cfg, src_dir):
    return {
        'cwlVersion': 'v1.2',
        'class': 'CommandLineTool',
        'baseCommand': ['python3', str((src_dir / 'validate_data.py').resolve())],
        'inputs': {
            'train_csv': {'type': 'File', 'inputBinding': {'prefix': '--train', 'position': 1}},
            'score_csv': {'type': 'File', 'inputBinding': {'prefix': '--score', 'position': 2}},
        },
        'arguments': _as_cli_arguments([
            '--id-col', cfg.id_col,
            '--target-col', cfg.target_col,
            '--numeric', ','.join(cfg.numeric_features),
            '--categorical', ','.join(cfg.categorical_features),
            '--out', 'outputs/validation_report.json',
        ]),
        'outputs': {
            'validation_report': {'type': 'File', 'outputBinding': {'glob': 'outputs/validation_report.json'}}
        },
        'requirements': _tool_requirements(),
    }


def cwl_tool_train(cfg, src_dir):
    return {
        'cwlVersion': 'v1.2',
        'class': 'CommandLineTool',
        'baseCommand': ['python3', str((src_dir / 'train_model.py').resolve())],
        'inputs': {
            'train_csv': {'type': 'File', 'inputBinding': {'prefix': '--train', 'position': 1}},
        },
        'arguments': _as_cli_arguments([
            '--id-col', cfg.id_col,
            '--target-col', cfg.target_col,
            '--numeric', ','.join(cfg.numeric_features),
            '--categorical', ','.join(cfg.categorical_features),
            '--algorithm', cfg.algorithm,
            '--test-size', str(cfg.test_size),
            '--random-state', str(cfg.random_state),
            '--threshold', str(cfg.threshold),
            '--cv-folds', str(cfg.cv_folds),
            '--model-out', cfg.model_file,
            '--report-out', cfg.report_file,
        ]),
        'outputs': {
            'model_file': {'type': 'File', 'outputBinding': {'glob': cfg.model_file}},
            'report_file': {'type': 'File', 'outputBinding': {'glob': cfg.report_file}},
        },
        'requirements': _tool_requirements(),
    }


def cwl_tool_score(cfg, src_dir):
    return {
        'cwlVersion': 'v1.2',
        'class': 'CommandLineTool',
        'baseCommand': ['python3', str((src_dir / 'score_cases.py').resolve())],
        'inputs': {
            'score_csv': {'type': 'File', 'inputBinding': {'prefix': '--score', 'position': 1}},
            'model_file': {'type': 'File', 'inputBinding': {'prefix': '--model-in', 'position': 2}},
        },
        'arguments': _as_cli_arguments([
            '--id-col', cfg.id_col,
            '--numeric', ','.join(cfg.numeric_features),
            '--categorical', ','.join(cfg.categorical_features),
            '--threshold', str(cfg.threshold),
            '--predictions-out', cfg.predictions_file,
        ]),
        'outputs': {
            'predictions_file': {'type': 'File', 'outputBinding': {'glob': cfg.predictions_file}}
        },
        'requirements': _tool_requirements(),
    }


def cwl_workflow(cfg):
    return {
        'cwlVersion': 'v1.2',
        'class': 'Workflow',
        'doc': f'Generated from LeadFlow DSL project {cfg.project}',
        'inputs': {
            'train_csv': 'File',
            'score_csv': 'File',
        },
        'outputs': {
            'validation_report': {'type': 'File', 'outputSource': 'validate/validation_report'},
            'model_file': {'type': 'File', 'outputSource': 'train/model_file'},
            'report_file': {'type': 'File', 'outputSource': 'train/report_file'},
            'predictions_file': {'type': 'File', 'outputSource': 'score/predictions_file'},
        },
        'steps': {
            'validate': {
                'run': 'validate_data.cwl',
                'in': {'train_csv': 'train_csv', 'score_csv': 'score_csv'},
                'out': ['validation_report']
            },
            'train': {
                'run': 'train_model.cwl',
                'in': {'train_csv': 'train_csv'},
                'out': ['model_file', 'report_file']
            },
            'score': {
                'run': 'score_cases.cwl',
                'in': {'score_csv': 'score_csv', 'model_file': 'train/model_file'},
                'out': ['predictions_file']
            }
        }
    }


def _infer_feature_groups(df: pd.DataFrame, id_col: str, target_col: str):
    excluded = {id_col, target_col}
    numeric = []
    categorical = []

    for col in df.columns:
        if col in excluded:
            continue

        series = df[col]
        if series.dropna().empty:
            continue

        lowered = str(col).strip().lower()
        if lowered in {"target", "label", "class", "y", "outcome", "qualified", "survived", "income", "churn", "default"} and col == target_col:
            continue

        # Try strong numeric detection first
        coerced = pd.to_numeric(series, errors="coerce")
        numeric_ratio = coerced.notna().mean()

        if pd.api.types.is_numeric_dtype(series) or numeric_ratio >= 0.85:
            numeric.append(col)
        else:
            categorical.append(col)

    # Final safety: never allow id/target to leak into features
    numeric = [c for c in dict.fromkeys(numeric) if c not in excluded]
    categorical = [c for c in dict.fromkeys(categorical) if c not in excluded and c not in numeric]
    return numeric, categorical


def _auto_generate_dsl_from_dataset(train_df: pd.DataFrame, score_df: pd.DataFrame, id_col: str, target_col: str):
    numeric, categorical = _infer_feature_groups(train_df, id_col, target_col)
    numeric = [c for c in numeric if c not in {id_col, target_col}]
    categorical = [c for c in categorical if c not in {id_col, target_col}]

    # ... other code to generate the DSL ...

    if target_col in numeric or target_col in categorical:
        raise ValueError(
            f"Target column '{target_col}' was incorrectly included in the feature list. "
            "Please review the dataset and edit the DSL manually."
        )

    # Assuming the function returns a tuple like (id_col, target_col, numeric, categorical, ...)
    return id_col, target_col, numeric, categorical


def generate_all(grammar_path: Path, dsl_path: Path, out_dir: Path):
    cfg = parse_leadflow(grammar_path, dsl_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    src_dir = (grammar_path.parent.parent / 'src').resolve()
    (out_dir / 'dsl_config.json').write_text(json.dumps(cfg.as_dict(), indent=2), encoding='utf-8')
    with open(out_dir / 'validate_data.cwl', 'w', encoding='utf-8') as f:
        yaml.safe_dump(cwl_tool_validate(cfg, src_dir), f, sort_keys=False)
    with open(out_dir / 'train_model.cwl', 'w', encoding='utf-8') as f:
        yaml.safe_dump(cwl_tool_train(cfg, src_dir), f, sort_keys=False)
    with open(out_dir / 'score_cases.cwl', 'w', encoding='utf-8') as f:
        yaml.safe_dump(cwl_tool_score(cfg, src_dir), f, sort_keys=False)
    with open(out_dir / 'workflow.cwl', 'w', encoding='utf-8') as f:
        yaml.safe_dump(cwl_workflow(cfg), f, sort_keys=False)

    inputs = {
        'train_csv': {'class': 'File', 'path': str((out_dir.parent / cfg.train_path).resolve())},
        'score_csv': {'class': 'File', 'path': str((out_dir.parent / cfg.score_path).resolve())},
    }
    with open(out_dir / 'inputs.yml', 'w', encoding='utf-8') as f:
        yaml.safe_dump(inputs, f, sort_keys=False)
    return cfg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--grammar', required=True)
    ap.add_argument('--dsl', required=True)
    ap.add_argument('--outdir', required=True)
    args = ap.parse_args()
    cfg = generate_all(Path(args.grammar), Path(args.dsl), Path(args.outdir))
    print(json.dumps(cfg.as_dict(), indent=2))


if __name__ == '__main__':
    main()
