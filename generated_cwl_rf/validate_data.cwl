cwlVersion: v1.2
class: CommandLineTool
baseCommand:
- python3
- /mnt/data/LeadFlowML_Project/src/validate_data.py
inputs:
  train_csv:
    type: File
    inputBinding:
      prefix: --train
      position: 1
  score_csv:
    type: File
    inputBinding:
      prefix: --score
      position: 2
arguments:
- --id-col
- lead_id
- --target-col
- qualified
- --numeric
- age,annual_income,website_visits,prior_purchases,support_tickets
- --categorical
- region,channel,loyalty_segment
- --out
- outputs/validation_report.json
outputs:
  validation_report:
    type: File
    outputBinding:
      glob: outputs/validation_report.json
requirements:
  InlineJavascriptRequirement: {}
