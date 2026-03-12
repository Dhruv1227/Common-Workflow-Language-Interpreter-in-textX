cwlVersion: v1.2
class: CommandLineTool
baseCommand:
- python3
- /mnt/data/LeadFlowML_Project/src/train_model.py
inputs:
  train_csv:
    type: File
    inputBinding:
      prefix: --train
      position: 1
arguments:
- --id-col
- lead_id
- --target-col
- qualified
- --numeric
- age,annual_income,website_visits,prior_purchases,support_tickets
- --categorical
- region,channel,loyalty_segment
- --algorithm
- logistic_regression
- --test-size
- '0.25'
- --random-state
- '42'
- --threshold
- '0.55'
- --cv-folds
- '5'
- --model-out
- artifacts/lead_model.joblib
- --report-out
- outputs/evaluation_report.json
outputs:
  model_file:
    type: File
    outputBinding:
      glob: artifacts/lead_model.joblib
  report_file:
    type: File
    outputBinding:
      glob: outputs/evaluation_report.json
requirements:
  InlineJavascriptRequirement: {}
