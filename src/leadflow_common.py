from __future__ import annotations
from pathlib import Path
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import csv
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from textx import metamodel_from_file


def _column_value(obj) -> str:
    value = getattr(obj, "value", obj)
    value = str(value)
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    return value


def _read_csv_auto(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;|\t")
            sep = dialect.delimiter
        except csv.Error:
            sep = ","
    return pd.read_csv(path, sep=sep)


def _normalize_binary_target(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        values = pd.Series(series).astype(int)
        unique_vals = sorted(pd.unique(values.dropna()))
        if set(unique_vals).issubset({0, 1}):
            return values
        if len(unique_vals) == 2:
            mapping = {unique_vals[0]: 0, unique_vals[1]: 1}
            return values.map(mapping).astype(int)
        raise ValueError(
            f"Numeric target '{series.name}' is not binary. Found values: {unique_vals}"
        )

    cleaned = series.astype(str).str.strip().str.lower()

    known_mapping = {
        "yes": 1,
        "no": 0,
        "true": 1,
        "false": 0,
        "1": 1,
        "0": 0,
        "recurrence-events": 1,
        "no-recurrence-events": 0,
        "positive": 1,
        "negative": 0,
        "success": 1,
        "failure": 0,
        "converted": 1,
        "not converted": 0,
        "<=50k": 0,
        ">50k": 1,
        "<=50k.": 0,
        ">50k.": 1,
        "qualified": 1,
        "not qualified": 0,
        "approved": 1,
        "rejected": 0,
        "survived": 1,
        "died": 0,
        "malignant": 1,
        "benign": 0,
    }

    unique_vals = sorted(cleaned.dropna().unique().tolist())

    # First try known labels
    if all(v in known_mapping for v in unique_vals):
        return cleaned.map(known_mapping).astype(int)

    # Generic fallback: any two unique classes -> map automatically
    if len(unique_vals) == 2:
        auto_map = {unique_vals[0]: 0, unique_vals[1]: 1}
        return cleaned.map(auto_map).astype(int)

    raise ValueError(
        f"Unsupported target labels found in '{series.name}': {unique_vals}. "
        "Please map them to binary values."
    )

def _ensure_id_column(df: pd.DataFrame, id_col: str | None = None) -> tuple[pd.DataFrame, str]:
    df = df.copy()

    if id_col and id_col in df.columns:
        return df, id_col

    generated_id = "record_id"
    counter = 1
    while generated_id in df.columns:
        generated_id = f"record_id_{counter}"
        counter += 1

    df.insert(0, generated_id, range(1, len(df) + 1))
    return df, generated_id


@dataclass
class LeadFlowConfig:
    project: str
    description: str
    train_path: str
    score_path: str
    id_col: str
    target_col: str
    numeric_features: List[str]
    categorical_features: List[str]
    algorithm: str
    test_size: float
    random_state: int
    threshold: float
    cv_folds: int
    metrics: List[str]
    model_file: str
    predictions_file: str
    report_file: str

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def parse_leadflow(grammar_path: str | Path, dsl_path: str | Path) -> LeadFlowConfig:
    mm = metamodel_from_file(str(grammar_path))
    model = mm.model_from_file(str(dsl_path))
    numeric = [_column_value(x) for x in model.features.numeric]
    categorical = [_column_value(x) for x in model.features.categorical]
    metrics = [m.value for m in model.metrics.metrics]
    cfg = LeadFlowConfig(
        project=model.name,
        description=model.description.strip('"'),
        train_path=model.data.train.strip('"'),
        score_path=model.data.score.strip('"'),
        id_col=_column_value(model.data.id_col),
        target_col=_column_value(model.data.target_col),
        numeric_features=numeric,
        categorical_features=categorical,
        algorithm=model.model.algorithm.value,
        test_size=float(model.model.test_size),
        random_state=int(model.model.random_state),
        threshold=float(model.model.threshold),
        cv_folds=int(model.model.cv_folds),
        metrics=metrics,
        model_file=model.outputs.model_file.strip('"'),
        predictions_file=model.outputs.predictions_file.strip('"'),
        report_file=model.outputs.report_file.strip('"'),
    )
    return cfg


def validate_config(cfg: LeadFlowConfig, train_df: pd.DataFrame, score_df: pd.DataFrame) -> dict:
    required_train = [cfg.id_col, cfg.target_col] + cfg.numeric_features + cfg.categorical_features
    required_score = [cfg.id_col] + cfg.numeric_features + cfg.categorical_features
    missing_train = [c for c in required_train if c not in train_df.columns]
    missing_score = [c for c in required_score if c not in score_df.columns]
    duplicates = sorted({c for c in cfg.numeric_features + cfg.categorical_features if (cfg.numeric_features + cfg.categorical_features).count(c) > 1})
    validation = {
        'project': cfg.project,
        'missing_train_columns': missing_train,
        'missing_score_columns': missing_score,
        'duplicate_features': duplicates,
        'train_rows': int(len(train_df)),
        'score_rows': int(len(score_df)),
        'train_ok': len(missing_train) == 0 and len(duplicates) == 0,
        'score_ok': len(missing_score) == 0 and len(duplicates) == 0,
    }
    return validation


def build_pipeline(cfg: LeadFlowConfig):
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, cfg.numeric_features),
            ('cat', categorical_transformer, cfg.categorical_features),
        ]
    )
    if cfg.algorithm == 'logistic_regression':
        estimator = LogisticRegression(max_iter=1000, random_state=cfg.random_state)
    elif cfg.algorithm == 'random_forest':
        estimator = RandomForestClassifier(n_estimators=250, max_depth=8, random_state=cfg.random_state)
    else:
        raise ValueError(f'Unsupported algorithm: {cfg.algorithm}')
    return Pipeline(steps=[('prep', preprocessor), ('model', estimator)])


def evaluate_predictions(y_true, y_prob, threshold: float) -> dict:
    y_true = np.asarray(y_true).astype(int)
    y_prob = np.asarray(y_prob, dtype=float)
    y_pred = (y_prob >= threshold).astype(int)

    result = {
        'accuracy': float(accuracy_score(y_true, y_pred)),
        'precision': float(precision_score(y_true, y_pred, zero_division=0)),
        'recall': float(recall_score(y_true, y_pred, zero_division=0)),
        'f1': float(f1_score(y_true, y_pred, zero_division=0)),
        'roc_auc': None,
    }

    if len(np.unique(y_true)) > 1:
        result['roc_auc'] = float(roc_auc_score(y_true, y_prob))

    return result


def run_training(cfg: LeadFlowConfig, root_dir: str | Path):
    root_dir = Path(root_dir)
    train_path = root_dir / cfg.train_path
    train_df = _read_csv_auto(train_path)

    if cfg.target_col not in train_df.columns:
        raise KeyError(
            f"Target column '{cfg.target_col}' not found in training data. "
            f"Available columns: {list(train_df.columns)}"
        )

    requested_id = cfg.id_col if getattr(cfg, "id_col", None) != cfg.target_col else None
    train_df, actual_id_col = _ensure_id_column(train_df, requested_id)

    feature_cols = cfg.numeric_features + cfg.categorical_features
    missing_features = [c for c in feature_cols if c not in train_df.columns]
    if missing_features:
        raise KeyError(
            f"Missing feature columns in training data: {missing_features}. "
            f"Available columns: {list(train_df.columns)}"
        )

    X = train_df[feature_cols]
    y = _normalize_binary_target(train_df[cfg.target_col])

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=cfg.test_size,
        random_state=cfg.random_state,
        stratify=y if y.nunique() == 2 else None,
    )

    pipeline = build_pipeline(cfg)
    pipeline.fit(X_train, y_train)

    if hasattr(pipeline, "predict_proba"):
        y_prob = pipeline.predict_proba(X_test)[:, 1]
    else:
        y_prob = pipeline.predict(X_test)

    metrics = evaluate_predictions(y_test.to_numpy(), y_prob, cfg.threshold)

    cv_scores = cross_val_score(pipeline, X, y, cv=cfg.cv_folds, scoring='f1')
    metrics['cv_f1_mean'] = float(cv_scores.mean())
    metrics['cv_f1_std'] = float(cv_scores.std())

    model_path = root_dir / cfg.model_file
    report_path = root_dir / cfg.report_file
    model_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(
        {
            'pipeline': pipeline,
            'config': cfg.as_dict(),
            'actual_id_col': actual_id_col,
        },
        model_path,
    )

    report = {
        'project': cfg.project,
        'algorithm': cfg.algorithm,
        'threshold': cfg.threshold,
        'metrics': metrics,
        'feature_count': len(feature_cols),
        'train_rows': int(len(train_df)),
        'test_rows': int(len(X_test)),
        'target_column': cfg.target_col,
        'id_column_used': actual_id_col,
    }
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


def run_scoring(cfg: LeadFlowConfig, root_dir: str | Path):
    root_dir = Path(root_dir)
    score_df = _read_csv_auto(root_dir / cfg.score_path)

    bundle = joblib.load(root_dir / cfg.model_file)
    pipeline = bundle['pipeline']
    actual_id_col = bundle.get('actual_id_col', getattr(cfg, 'id_col', None))

    safe_requested_id = actual_id_col if actual_id_col != cfg.target_col else None
    score_df, actual_id_col = _ensure_id_column(score_df, safe_requested_id)

    feature_cols = cfg.numeric_features + cfg.categorical_features
    missing_features = [c for c in feature_cols if c not in score_df.columns]
    if missing_features:
        raise KeyError(
            f"Missing feature columns in scoring data: {missing_features}. "
            f"Available columns: {list(score_df.columns)}"
        )

    X_score = score_df[feature_cols]

    if hasattr(pipeline, 'predict_proba'):
        probs = pipeline.predict_proba(X_score)[:, 1]
    else:
        preds = pipeline.predict(X_score)
        probs = np.asarray(preds, dtype=float)

    preds = (np.asarray(probs) >= cfg.threshold).astype(int)

    output = pd.DataFrame()
    output[actual_id_col] = score_df[actual_id_col].values
    output['qualified_probability'] = np.round(probs, 4)
    output['predicted_class'] = preds

    pred_path = root_dir / cfg.predictions_file
    pred_path.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(pred_path, index=False)
    return output