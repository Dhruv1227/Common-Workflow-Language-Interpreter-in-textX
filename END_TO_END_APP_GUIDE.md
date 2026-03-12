# LeadFlowML End-to-End App Guide

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## New auto-specification flow
1. Upload a training CSV.
2. Optionally upload a scoring CSV.
3. Click **Auto-generate DSL from dataset**.
4. The app infers:
   - ID column
   - target column
   - numeric features
   - categorical features
   - recommended ML algorithm
5. Review the generated DSL and run the pipeline.

The grammar now supports quoted column names, so datasets with spaces or mixed naming styles are easier to use.
