cwlVersion: v1.2
class: Workflow
doc: Generated from LeadFlow DSL project LeadQualificationRF
inputs:
  train_csv: File
  score_csv: File
outputs:
  validation_report:
    type: File
    outputSource: validate/validation_report
  model_file:
    type: File
    outputSource: train/model_file
  report_file:
    type: File
    outputSource: train/report_file
  predictions_file:
    type: File
    outputSource: score/predictions_file
steps:
  validate:
    run: validate_data.cwl
    in:
      train_csv: train_csv
      score_csv: score_csv
    out:
    - validation_report
  train:
    run: train_model.cwl
    in:
      train_csv: train_csv
    out:
    - model_file
    - report_file
  score:
    run: score_cases.cwl
    in:
      score_csv: score_csv
      model_file: train/model_file
    out:
    - predictions_file
