from pathlib import Path
import nbformat as nbf

root = Path('/mnt/data/LeadFlowML_Project')
nb = nbf.v4.new_notebook()

cells = []

cells.append(nbf.v4.new_markdown_cell("""# LeadFlowML DSL Demo\n\nThis notebook demonstrates an end-to-end **sales lead classification DSL** built with **textX** and exported into **CWL**. The workflow trains on historical CRM cases and classifies new sales cases.\n\nScenarios covered:\n1. Parse the DSL into a Python object model\n2. Generate CWL tools + workflow\n3. Run the default logistic-regression pipeline\n4. Compare an alternative random-forest scenario\n5. Execute the generated CWL workflow\n"""))

cells.append(nbf.v4.new_code_cell("""from pathlib import Path\nimport json\nimport subprocess\nimport pandas as pd\nimport matplotlib.pyplot as plt\n\nROOT = Path('/mnt/data/LeadFlowML_Project')\nimport os, sys\nos.chdir(ROOT)\nsys.path.append(str(ROOT / 'src'))\n\nfrom leadflow_common import parse_leadflow, validate_config, run_training, run_scoring\nfrom dsl_processor import generate_all\n"""))

cells.append(nbf.v4.new_markdown_cell("## 1) Parse the default DSL scenario"))

cells.append(nbf.v4.new_code_cell("""grammar = ROOT / 'dsl' / 'leadflow.tx'\ndefault_dsl = ROOT / 'workflows' / 'lead_qualification.leadflow'\ncfg = parse_leadflow(grammar, default_dsl)\npd.DataFrame([cfg.as_dict()]).T\n"""))

cells.append(nbf.v4.new_markdown_cell("## 2) Generate CWL files from the DSL"))

cells.append(nbf.v4.new_code_cell("""generated_dir = ROOT / 'generated_cwl'\ngenerate_all(grammar, default_dsl, generated_dir)\n[p.name for p in sorted(generated_dir.iterdir())]\n"""))

cells.append(nbf.v4.new_code_cell("""print((generated_dir / 'workflow.cwl').read_text()[:1000])\n"""))

cells.append(nbf.v4.new_markdown_cell("## 3) Run the default local pipeline"))

cells.append(nbf.v4.new_code_cell("""train_df = pd.read_csv(ROOT / cfg.train_path)\nscore_df = pd.read_csv(ROOT / cfg.score_path)\nvalidation = validate_config(cfg, train_df, score_df)\nvalidation\n"""))

cells.append(nbf.v4.new_code_cell("""report_default = run_training(cfg, ROOT)\npreds_default = run_scoring(cfg, ROOT)\nreport_default\n"""))

cells.append(nbf.v4.new_code_cell("""preds_default.head(10)\n"""))

cells.append(nbf.v4.new_markdown_cell("## 4) Alternative scenario: random forest"))

cells.append(nbf.v4.new_code_cell("""alt_dsl = ROOT / 'workflows' / 'lead_qualification_rf.leadflow'\ncfg_rf = parse_leadflow(grammar, alt_dsl)\nreport_rf = run_training(cfg_rf, ROOT)\npreds_rf = run_scoring(cfg_rf, ROOT)\nreport_rf\n"""))

cells.append(nbf.v4.new_code_cell("""comparison = pd.DataFrame({\n    'metric': ['accuracy', 'precision', 'recall', 'f1', 'roc_auc', 'cv_f1_mean'],\n    'logistic_regression': [\n        report_default['metrics']['accuracy'],\n        report_default['metrics']['precision'],\n        report_default['metrics']['recall'],\n        report_default['metrics']['f1'],\n        report_default['metrics']['roc_auc'],\n        report_default['metrics']['cv_f1_mean'],\n    ],\n    'random_forest': [\n        report_rf['metrics']['accuracy'],\n        report_rf['metrics']['precision'],\n        report_rf['metrics']['recall'],\n        report_rf['metrics']['f1'],\n        report_rf['metrics']['roc_auc'],\n        report_rf['metrics']['cv_f1_mean'],\n    ]\n})\ncomparison\n"""))

cells.append(nbf.v4.new_code_cell("""artifacts = ROOT / 'artifacts'\nartifacts.mkdir(exist_ok=True)\n\nax = comparison.set_index('metric').plot(kind='bar', figsize=(10, 5), title='Model comparison on the sales lead scenario')\nax.set_ylabel('score')\nax.figure.tight_layout()\nplt.savefig(artifacts / 'metrics_comparison.png', dpi=160)\nplt.show()\n"""))

cells.append(nbf.v4.new_code_cell("""plt.figure(figsize=(8, 5))\nplt.hist(preds_default['qualified_probability'], bins=8)\nplt.title('Probability distribution for new sales cases (default scenario)')\nplt.xlabel('qualified_probability')\nplt.ylabel('count')\nplt.tight_layout()\nplt.savefig(artifacts / 'prediction_distribution.png', dpi=160)\nplt.show()\n"""))

cells.append(nbf.v4.new_markdown_cell("## 5) Execute the generated CWL workflow"))

cells.append(nbf.v4.new_code_cell("""res = subprocess.run(['cwltool', 'workflow.cwl', 'inputs.yml'], cwd=generated_dir, capture_output=True, text=True)\nprint(res.stdout[-2500:])\nprint('returncode =', res.returncode)\n"""))

cells.append(nbf.v4.new_code_cell("""output_files = ['validation_report.json', 'evaluation_report.json', 'new_case_predictions.csv']\n{k: (generated_dir / k).exists() for k in output_files}\n"""))

cells.append(nbf.v4.new_markdown_cell("## 6) Summary\n\n- The DSL is concise enough for domain experts to read and modify.\n- textX handles parsing + model creation.\n- The processor turns the DSL into reusable CWL CommandLineTools and a Workflow.\n- The same domain specification supports both **local execution** and **portable workflow execution** through CWL.\n"""))

nb['cells'] = cells
nb['metadata'] = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.13"}}

out = root / 'notebooks' / 'LeadFlowML_demo.ipynb'
nbf.write(nb, out)
print(out)
