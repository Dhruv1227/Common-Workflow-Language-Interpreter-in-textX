import json
import re
import shutil
import sys
import tempfile
import zipfile
import csv
import subprocess
import io
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from leadflow_common import parse_leadflow, validate_config, run_training, run_scoring
import dsl_processor as dslproc

st.set_page_config(page_title="LeadFlowML Studio", layout="wide")

DEFAULT_GRAMMAR = ROOT / "dsl" / "leadflow.tx"
DEFAULT_DSL = ROOT / "workflows" / "lead_qualification.leadflow"
DEFAULT_TRAIN = ROOT / "data" / "train_sales_cases.csv"
DEFAULT_SCORE = ROOT / "data" / "new_sales_cases.csv"


def _write_uploaded(uploaded_file, destination: Path):
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(uploaded_file.getvalue())


def _read_csv_auto(source) -> pd.DataFrame:
    if hasattr(source, "getvalue"):
        raw = source.getvalue()
    else:
        raw = Path(source).read_bytes()

    text = raw.decode("utf-8", errors="ignore")
    sample = text[:5000]

    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;|\t")
        sep = dialect.delimiter
    except csv.Error:
        sep = ";" if sample.count(";") > sample.count(",") else ","

    df = pd.read_csv(io.StringIO(text), sep=sep)
    df.columns = [str(c).strip().strip('"').strip("'") for c in df.columns]
    df = df.dropna(axis=1, how="all")
    return df


def _write_normalized_csv(uploaded_file, destination: Path):
    destination.parent.mkdir(parents=True, exist_ok=True)
    df = _read_csv_auto(uploaded_file)
    df.to_csv(destination, index=False)


def _render_metric_cards(report: dict):
    metrics = report.get("metrics", {})
    cols = st.columns(5)
    ordered = [("accuracy", "Accuracy"), ("precision", "Precision"), ("recall", "Recall"), ("f1", "F1"), ("roc_auc", "ROC AUC")]
    for col, (key, label) in zip(cols, ordered):
        val = metrics.get(key)
        col.metric(label, f"{val:.3f}" if isinstance(val, (int, float)) else "—")


def _plot_prediction_distribution(predictions_df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(7, 4))

    # try to detect a probability column automatically
    prob_col = None
    for candidate in [
        "qualified_probability",
        "probability",
        "predicted_probability",
        "score",
        "prediction_probability",
    ]:
        if candidate in predictions_df.columns:
            prob_col = candidate
            break

    if prob_col:
        predictions_df[prob_col].hist(ax=ax, bins=12)
        ax.set_title("Prediction Probability Distribution")
        ax.set_xlabel(prob_col)
        ax.set_ylabel("Count")

    elif "predicted_class" in predictions_df.columns:
        predictions_df["predicted_class"].value_counts().sort_index().plot(kind="bar", ax=ax)
        ax.set_title("Predicted Class Distribution")
        ax.set_xlabel("Predicted Class")
        ax.set_ylabel("Count")

    else:
        ax.text(
            0.5,
            0.5,
            f"No probability column found. Available columns: {list(predictions_df.columns)}",
            ha="center",
            va="center",
            wrap=True,
        )
        ax.set_axis_off()

    st.pyplot(fig)
    plt.close(fig)



def _make_zip(folder: Path) -> bytes:
    temp_zip = folder / "session_bundle.zip"
    with zipfile.ZipFile(temp_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in folder.rglob("*"):
            if path.is_file() and path.name != temp_zip.name:
                zf.write(path, path.relative_to(folder))
    data = temp_zip.read_bytes()
    temp_zip.unlink(missing_ok=True)
    return data


def _write_cwl_inputs(outdir: Path, cfg):
    inputs = {
        "train_csv": {"class": "File", "path": str((outdir.parent / cfg.train_path).resolve())},
        "score_csv": {"class": "File", "path": str((outdir.parent / cfg.score_path).resolve())},
    }
    import yaml
    with open(outdir / "inputs.yml", "w", encoding="utf-8") as f:
        yaml.safe_dump(inputs, f, sort_keys=False)
    return outdir / "inputs.yml"


def _run_cwl_workflow(workdir: Path, workflow_path: Path, inputs_path: Path):
    try:
        result = subprocess.run(
            ["cwltool", str(workflow_path.resolve()), str(inputs_path.resolve())],
            cwd=str(workdir),
            capture_output=True,
            text=True,
            check=True,
        )
        return {
            "ok": True,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except FileNotFoundError:
        return {
            "ok": False,
            "stdout": "",
            "stderr": "cwltool is not installed or not available on PATH. Install it with: pip install cwltool",
        }
    except subprocess.CalledProcessError as e:
        return {
            "ok": False,
            "stdout": e.stdout,
            "stderr": e.stderr,
        }


def _dsl_value(value: str) -> str:
    value = str(value)
    return json.dumps(value)


def _clean_project_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", name)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned:
        cleaned = "AutoGeneratedProject"
    if cleaned[0].isdigit():
        cleaned = f"Project_{cleaned}"
    return cleaned


def _detect_id_column(df: pd.DataFrame) -> str:
    candidates = [c for c in df.columns if c.lower() in {"id", "lead_id", "customer_id", "case_id", "record_id", "passengerid"}]
    if candidates:
        return candidates[0]

    uniqueness = []
    for col in df.columns:
        # do not treat obvious target-like names as IDs
        if str(col).strip().lower() in {"target", "label", "class", "y", "outcome", "qualified", "survived", "income", "churn", "default"}:
            continue
        ratio = df[col].nunique(dropna=False) / max(len(df), 1)
        if ratio >= 0.98:
            uniqueness.append(col)

    return uniqueness[0] if uniqueness else "record_id"


def _detect_target_column(df: pd.DataFrame, id_col: str) -> str:
    preferred_names = {
        "target", "label", "class", "y", "outcome", "qualified", "survived",
        "income", "churn", "default", "approved", "converted", "response"
    }

    # 1. Prefer well-known target names, but only if they are truly binary
    for col in df.columns:
        if col == id_col:
            continue
        col_norm = str(col).strip().lower()
        unique_count = df[col].dropna().nunique()
        if col_norm in preferred_names and unique_count == 2:
            return col

    # 2. Otherwise collect only binary columns
    binary_candidates = []
    for col in df.columns:
        if col == id_col:
            continue
        unique_count = df[col].dropna().nunique()
        if unique_count == 2:
            binary_candidates.append(col)

    # 3. If exactly one binary column exists, use it
    if len(binary_candidates) == 1:
        return binary_candidates[0]

    # 4. If several binary columns exist, prefer one closer to the end of the dataset
    if len(binary_candidates) > 1:
        return binary_candidates[-1]

    # 5. No safe target found
    raise ValueError(
        "Could not infer a binary target column automatically. "
        "Please review the dataset and edit the DSL manually."
    )


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

        # Try numeric detection
        coerced = pd.to_numeric(series, errors="coerce")
        numeric_ratio = coerced.notna().mean()

        if pd.api.types.is_numeric_dtype(series) or numeric_ratio >= 0.85:
            numeric.append(col)
        else:
            categorical.append(col)

    # Final safety (VERY IMPORTANT)
    numeric = [c for c in numeric if c not in excluded]
    categorical = [c for c in categorical if c not in excluded and c not in numeric]

    return numeric, categorical

def _prepare_schema_from_user_choice(train_df: pd.DataFrame, target_col: str, id_col_choice: str):
    df = train_df.copy()

    if id_col_choice == "<auto-generate record_id>":
        id_col = "record_id"
        if id_col in df.columns:
            base = id_col
            i = 1
            while id_col in df.columns:
                id_col = f"{base}_{i}"
                i += 1
        df.insert(0, id_col, range(1, len(df) + 1))
    else:
        id_col = id_col_choice

    numeric, categorical = _infer_feature_groups(df, id_col, target_col)

    numeric = [c for c in numeric if c not in {id_col, target_col}]
    categorical = [c for c in categorical if c not in {id_col, target_col}]

    if target_col in numeric or target_col in categorical:
        raise ValueError(
            f"Target column '{target_col}' was incorrectly included in features."
        )

    return df, id_col, numeric, categorical

def _auto_generate_dsl_from_dataset(train_df: pd.DataFrame, train_path: str = "data/train.csv", score_path: str = "data/score.csv") -> tuple[str, dict]:
    id_col = _detect_id_column(train_df)
    target_col = _detect_target_column(train_df, id_col)
    if target_col == id_col:
        raise ValueError(
            f"The inferred target column '{target_col}' is the same as the ID column. "
            "Please review the dataset and edit the DSL manually."
        )
    numeric, categorical = _infer_feature_groups(train_df, id_col, target_col)

    if not numeric and not categorical:
        raise ValueError("No usable feature columns were found after excluding the inferred ID and target columns.")

    algorithm = "logistic_regression" if len(numeric) >= len(categorical) else "random_forest"
    project_name = _clean_project_name(Path(train_path).stem + "_pipeline")
    description = f"Auto-generated DSL specification inferred from dataset schema with {len(numeric)} numeric and {len(categorical)} categorical features."

    numeric_line = ", ".join(_dsl_value(col) for col in numeric) if numeric else _dsl_value("__none__")
    categorical_line = ", ".join(_dsl_value(col) for col in categorical) if categorical else _dsl_value("__none__")

    dsl_text = f"""project {project_name}
description {_dsl_value(description)}
data
train {_dsl_value(train_path)}
score {_dsl_value(score_path)}
id {_dsl_value(id_col)}
target {_dsl_value(target_col)}
features
numeric {numeric_line}
categorical {categorical_line}
model
algorithm {algorithm}
test_size 0.20
random_state 42
threshold 0.50
cv_folds 5
metrics accuracy, precision, recall, f1, roc_auc
outputs
model_file "artifacts/{project_name}_model.joblib"
predictions_file "outputs/{project_name}_predictions.csv"
report_file "outputs/{project_name}_report.json"
"""
    details = {
        "id_column": id_col,
        "target_column": target_col,
        "numeric_features": numeric,
        "categorical_features": categorical,
        "recommended_algorithm": algorithm,
    }
    return dsl_text, details


st.title("LeadFlowML Studio")
st.caption("End-to-end application for DSL-driven machine learning workflows built with textX and generated into CWL assets.")

with st.sidebar:
    st.header("Inputs")
    mode = st.radio("Source mode", ["Use bundled example", "Upload my own files"], index=0)
    uploaded_dsl = st.file_uploader("DSL file (.leadflow)", type=["leadflow", "txt"])
    uploaded_train = st.file_uploader("Training CSV", type=["csv"])
    uploaded_score = st.file_uploader("Scoring CSV", type=["csv"])
    auto_generate = st.button("Auto-generate DSL from dataset", use_container_width=True)
    run_generation = st.button("Run end-to-end pipeline", type="primary", use_container_width=True)
    generate_only_cwl = st.button("Generate CWL only", use_container_width=True)

if "dsl_text" not in st.session_state:
    st.session_state.dsl_text = DEFAULT_DSL.read_text(encoding="utf-8")

if uploaded_dsl is not None:
    st.session_state.dsl_text = uploaded_dsl.getvalue().decode("utf-8")

selected_target = None
selected_id = None
preview_df = None

if mode == "Use bundled example":
    preview_df = _read_csv_auto(DEFAULT_TRAIN)
elif uploaded_train is not None:
    preview_df = _read_csv_auto(uploaded_train)

if preview_df is not None:
    st.subheader("Dataset preview")
    st.dataframe(preview_df.head(), use_container_width=True)

    target_options = list(preview_df.columns)
    default_target_index = target_options.index("y") if "y" in target_options else 0

    selected_target = st.selectbox(
        "Select target column",
        target_options,
        index=default_target_index,
    )

    id_options = ["<auto-generate record_id>"] + list(preview_df.columns)
    default_id_index = 0
    for preferred_id in ["record_id", "id", "customer_id", "lead_id", "case_id", "PassengerId"]:
        if preferred_id in preview_df.columns:
            default_id_index = id_options.index(preferred_id)
            break

    selected_id = st.selectbox(
        "Select ID column (optional)",
        id_options,
        index=default_id_index,
    )

if auto_generate:
    try:
        if preview_df is None:
            st.error("Upload or load a training CSV first.")
            st.stop()

        if selected_target is None or selected_id is None:
            st.error("Please select a target column and ID option first.")
            st.stop()

        prepared_df, id_col, numeric, categorical = _prepare_schema_from_user_choice(
            preview_df,
            selected_target,
            selected_id,
        )

        if mode == "Use bundled example":
            train_path = f"data/{DEFAULT_TRAIN.name}"
            score_path = f"data/{DEFAULT_SCORE.name}"
        else:
            score_name = uploaded_score.name if uploaded_score is not None else "score.csv"
            train_path = "data/train.csv"
            score_path = f"data/{score_name}"

        algorithm = "logistic_regression" if len(numeric) >= len(categorical) else "random_forest"
        project_name = _clean_project_name(Path(train_path).stem + "_pipeline")
        description = f"User-guided DSL specification with target '{selected_target}', {len(numeric)} numeric and {len(categorical)} categorical features."

        numeric_line = ", ".join(_dsl_value(col) for col in numeric) if numeric else _dsl_value("__none__")
        categorical_line = ", ".join(_dsl_value(col) for col in categorical) if categorical else _dsl_value("__none__")

        generated_dsl = f'''project {project_name}
description {_dsl_value(description)}
data
train {_dsl_value(train_path)}
score {_dsl_value(score_path)}
id {_dsl_value(id_col)}
target {_dsl_value(selected_target)}
features
numeric {numeric_line}
categorical {categorical_line}
model
algorithm {algorithm}
test_size 0.20
random_state 42
threshold 0.50
cv_folds 5
metrics accuracy, precision, recall, f1, roc_auc
outputs
model_file "artifacts/{project_name}_model.joblib"
predictions_file "outputs/{project_name}_predictions.csv"
report_file "outputs/{project_name}_report.json"
'''

        schema_info = {
            "id_column": id_col,
            "target_column": selected_target,
            "numeric_features": numeric,
            "categorical_features": categorical,
            "recommended_algorithm": algorithm,
        }

        st.session_state.dsl_text = generated_dsl
        st.success("DSL specification was generated from your selected target and ID settings.")
        st.json(schema_info)

    except Exception as exc:
        st.error(f"Automatic DSL generation failed: {exc}")
                
st.subheader("1) DSL specification")
dsl_text = st.text_area("Edit the DSL and rerun the workflow", value=st.session_state.dsl_text, height=420)
st.session_state.dsl_text = dsl_text

with st.expander("How the automatic DSL generation works"):
    st.write(
        "The app inspects the uploaded training dataset, detects a likely ID column, selects a likely target column, "
        "splits the remaining columns into numeric and categorical features, and then writes a valid LeadFlow DSL specification for you."
    )

if run_generation or generate_only_cwl:
    with tempfile.TemporaryDirectory() as tmpdir:
        workdir = Path(tmpdir)
        for rel in ["dsl", "workflows", "data", "outputs", "artifacts", "generated_cwl", "src"]:
            (workdir / rel).mkdir(parents=True, exist_ok=True)

        shutil.copy(DEFAULT_GRAMMAR, workdir / "dsl" / "leadflow.tx")
        for src_file in (ROOT / "src").glob("*.py"):
            shutil.copy(src_file, workdir / "src" / src_file.name)

        (workdir / "workflows" / "session.leadflow").write_text(dsl_text, encoding="utf-8")

        if mode == "Use bundled example":
            shutil.copy(DEFAULT_TRAIN, workdir / "data" / DEFAULT_TRAIN.name)
            shutil.copy(DEFAULT_SCORE, workdir / "data" / DEFAULT_SCORE.name)
        else:
            if uploaded_train is None or uploaded_score is None:
                st.error("Please upload both training and scoring CSV files.")
                st.stop()
            _write_normalized_csv(uploaded_train, workdir / "data" / "train.csv")
            _write_normalized_csv(uploaded_score, workdir / "data" / uploaded_score.name)

        try:
            cfg = parse_leadflow(workdir / "dsl" / "leadflow.tx", workdir / "workflows" / "session.leadflow")
        except Exception as exc:
            st.error(f"DSL parsing failed: {exc}")
            st.stop()

        st.subheader("2) Parsed configuration")
        st.json(cfg.as_dict())

        train_df = _read_csv_auto(workdir / cfg.train_path)
        score_df = _read_csv_auto(workdir / cfg.score_path)
        validation = validate_config(cfg, train_df, score_df)

        st.subheader("3) Validation report")
        st.json(validation)

        outdir = workdir / "generated_cwl"
        outdir.mkdir(exist_ok=True)

        validate_doc = dslproc.cwl_tool_validate(cfg, workdir / "src")
        train_doc = dslproc.cwl_tool_train(cfg, workdir / "src")
        score_doc = dslproc.cwl_tool_score(cfg, workdir / "src")
        workflow_doc = dslproc.cwl_workflow(cfg)

        import yaml
        for name, doc in {
            "validate_data.cwl": validate_doc,
            "train_model.cwl": train_doc,
            "score_cases.cwl": score_doc,
            "workflow.cwl": workflow_doc,
        }.items():
            with open(outdir / name, "w", encoding="utf-8") as f:
                yaml.safe_dump(doc, f, sort_keys=False)

        inputs_path = _write_cwl_inputs(outdir, cfg)
        (outdir / "dsl_config.json").write_text(json.dumps(cfg.as_dict(), indent=2), encoding="utf-8")

        st.subheader("4) Generated CWL assets")
        cols = st.columns(2)
        with cols[0]:
            st.code((outdir / "workflow.cwl").read_text(encoding="utf-8"), language="yaml")
        with cols[1]:
            st.code((outdir / "inputs.yml").read_text(encoding="utf-8"), language="yaml")

        cwl_zip = _make_zip(outdir)
        st.download_button("Download generated CWL bundle", data=cwl_zip, file_name="leadflow_cwl_bundle.zip", mime="application/zip")

        st.subheader("5) CWL execution with cwltool")
        cwl_result = _run_cwl_workflow(workdir, outdir / "workflow.cwl", inputs_path)
        if cwl_result["ok"]:
            st.success("CWL workflow executed successfully with cwltool.")
            if cwl_result["stdout"]:
                st.code(cwl_result["stdout"], language="text")
            if cwl_result["stderr"]:
                st.code(cwl_result["stderr"], language="text")
        else:
            st.warning("CWL workflow execution did not complete successfully.")
            if cwl_result["stderr"]:
                st.code(cwl_result["stderr"], language="text")
            if cwl_result["stdout"]:
                st.code(cwl_result["stdout"], language="text")

        if not generate_only_cwl:
            report = run_training(cfg, workdir)
            predictions = run_scoring(cfg, workdir)

            st.subheader("6) Training summary")
            _render_metric_cards(report)
            st.json(report)

            st.subheader("7) Scored cases")
            st.dataframe(predictions, use_container_width=True)
            _plot_prediction_distribution(predictions)

            st.download_button(
                "Download predictions CSV",
                data=(workdir / cfg.predictions_file).read_bytes(),
                file_name=Path(cfg.predictions_file).name,
                mime="text/csv"
            )
            st.download_button(
                "Download evaluation report",
                data=(workdir / cfg.report_file).read_bytes(),
                file_name=Path(cfg.report_file).name,
                mime="application/json"
            )

with st.expander("How to run locally"):
    st.code(
        "pip install -r requirements.txt\n"
        "pip install cwltool\n"
        "streamlit run app.py",
        language="bash",
    )
