cwlVersion: v1.2
class: CommandLineTool
baseCommand:
- python3
- /mnt/data/LeadFlowML_Project/src/score_cases.py
inputs:
  score_csv:
    type: File
    inputBinding:
      prefix: --score
      position: 1
  model_file:
    type: File
    inputBinding:
      prefix: --model-in
      position: 2
arguments:
- --id-col
- lead_id
- --numeric
- age,annual_income,website_visits,prior_purchases,support_tickets
- --categorical
- region,channel,loyalty_segment
- --threshold
- '0.7'
- --predictions-out
- outputs/new_case_predictions_rf.csv
outputs:
  predictions_file:
    type: File
    outputBinding:
      glob: outputs/new_case_predictions_rf.csv
requirements:
  InlineJavascriptRequirement: {}
