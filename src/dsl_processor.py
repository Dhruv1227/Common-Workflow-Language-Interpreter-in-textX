
from __future__ import annotations
import argparse
import json
from pathlib import Path
import textwrap
import yaml
from leadflow_common import parse_leadflow


def cwl_tool_validate(cfg, src_dir):
    return {
        'cwlVersion': 'v1.2',
        'class': 'CommandLineTool',
        'baseCommand': ['python3', str(src_dir / 'validate_data.py')],
        'inputs': {
            'train_csv': {'type': 'File', 'inputBinding': {'prefix': '--train', 'position': 1}},
            'score_csv': {'type': 'File', 'inputBinding': {'prefix': '--score', 'position': 2}},
        },
        'arguments': [
            '--id-col', cfg.id_col,
            '--target-col', cfg.target_col,
            '--numeric', ','.join(cfg.numeric_features),
            '--categorical', ','.join(cfg.categorical_features),
            '--out', 'outputs/validation_report.json',
        ],
        'outputs': {
            'validation_report': {'type': 'File', 'outputBinding': {'glob': 'outputs/validation_report.json'}}
        },
        'requirements': {'InlineJavascriptRequirement': {}}
    }


def cwl_tool_train(cfg, src_dir):
    return {
        'cwlVersion': 'v1.2',
        'class': 'CommandLineTool',
        'baseCommand': ['python3', str(src_dir / 'train_model.py')],
        'inputs': {
            'train_csv': {'type': 'File', 'inputBinding': {'prefix': '--train', 'position': 1}},
        },
        'arguments': [
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
        ],
        'outputs': {
            'model_file': {'type': 'File', 'outputBinding': {'glob': cfg.model_file}},
            'report_file': {'type': 'File', 'outputBinding': {'glob': cfg.report_file}},
        },
        'requirements': {'InlineJavascriptRequirement': {}}
    }


def cwl_tool_score(cfg, src_dir):
    return {
        'cwlVersion': 'v1.2',
        'class': 'CommandLineTool',
        'baseCommand': ['python3', str(src_dir / 'score_cases.py')],
        'inputs': {
            'score_csv': {'type': 'File', 'inputBinding': {'prefix': '--score', 'position': 1}},
            'model_file': {'type': 'File', 'inputBinding': {'prefix': '--model-in', 'position': 2}},
        },
        'arguments': [
            '--id-col', cfg.id_col,
            '--numeric', ','.join(cfg.numeric_features),
            '--categorical', ','.join(cfg.categorical_features),
            '--threshold', str(cfg.threshold),
            '--predictions-out', cfg.predictions_file,
        ],
        'outputs': {
            'predictions_file': {'type': 'File', 'outputBinding': {'glob': cfg.predictions_file}}
        },
        'requirements': {'InlineJavascriptRequirement': {}}
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
        'train_csv': {'class': 'File', 'path': '../' + cfg.train_path},
        'score_csv': {'class': 'File', 'path': '../' + cfg.score_path},
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
