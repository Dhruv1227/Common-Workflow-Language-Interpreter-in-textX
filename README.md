
# LeadFlowML: Dataset-Driven DSL for Machine Learning Workflows

## Project Overview
LeadFlowML is an end-to-end application that demonstrates how a **Domain-Specific Language (DSL)** can be automatically generated from a dataset and used to define and execute a machine learning workflow.

The system:
1. Uploads a dataset
2. Automatically analyzes its schema
3. Generates a DSL specification
4. Parses the DSL using **textX**
5. Trains a machine learning model
6. Classifies new cases
7. Generates a **Common Workflow Language (CWL)** representation

This project demonstrates how DSLs can simplify complex workflows for domain experts.

---

# Architecture

User Dataset
      ↓
Schema Detection
      ↓
Auto DSL Generation
      ↓
textX Parser
      ↓
ML Pipeline (Scikit-learn)
      ↓
Prediction + Metrics
      ↓
CWL Workflow Generation

---

# Features

- Automatic DSL generation from dataset structure  
- textX based DSL parsing  
- Machine learning pipeline (Random Forest / Logistic Regression)  
- Model evaluation metrics (Accuracy, Precision, Recall, F1)  
- Prediction for new data  
- CWL workflow generation for reproducibility  
- Interactive Streamlit interface  

---

# Project Structure

LeadFlowML_EndToEndApp/

app.py  
requirements.txt  
README.md  

src/  
    leadflow_common.py  

dsl/  
    leadflow.tx  

data/  
    bank.csv  
    test.csv  

outputs/  
    model.joblib  
    predictions.csv  
    report.json  
    workflow.cwl  

notebooks/  
    demo.ipynb  

---

# Installation

## 1. Clone or Download the Project

Download the project folder:

LeadFlowML_EndToEndApp

## 2. Create Virtual Environment

Mac / Linux

python3 -m venv venv

Windows

python -m venv venv

## 3. Activate Environment

Mac / Linux

source venv/bin/activate

Windows

venv\Scripts\activate

## 4. Install Dependencies

pip install -r requirements.txt

---

# Running the Application

Start the Streamlit application:

streamlit run app.py

Then open your browser:

http://localhost:8501

---

# How to Use the Application

1. Select **Upload my own files**
2. Upload the **training dataset (bank.csv)**
3. Upload the **scoring dataset (test.csv)**
4. Click **Auto-generate DSL from dataset**
5. Review generated DSL
6. Click **Run end-to-end pipeline**

The system will automatically:

- parse DSL using textX  
- train the ML model  
- evaluate metrics  
- predict new cases  
- generate CWL workflow  

---

# Example DSL Generated

workflow BankMarketingPrediction {

dataset train_data "bank.csv"
dataset test_data "test.csv"

target "y"

numeric "age"
numeric "balance"
numeric "duration"
numeric "campaign"

categorical "job"
categorical "marital"
categorical "education"

model random_forest

}

---

# Dataset

This project uses the **Bank Marketing Dataset** from the UCI Machine Learning Repository.

Goal:
Predict whether a client will subscribe to a bank term deposit.

Target column:

y → yes / no

Reference:

Moro, S., Cortez, P., & Rita, P. (2014).  
A Data-Driven Approach to Predict the Success of Bank Telemarketing.  
Decision Support Systems.

---

# Outputs

After execution the system generates:

predictions.csv → predicted results  
report.json → evaluation metrics  
model.joblib → trained model  
workflow.cwl → workflow specification  

---

# Technologies Used

Python  
Streamlit  
textX  
Scikit-learn  
Pandas  
NumPy  
Joblib  

---

# Academic Purpose

This project was developed for a **Domain-Specific Language (DSL) programming language contest**.

Objective:
Design and implement a DSL capable of describing and executing machine learning workflows automatically from datasets.

---

# LeadFlowML

## Dataset‑Driven DSL for Machine Learning Workflows

LeadFlowML is an end‑to‑end application that demonstrates how a **Domain‑Specific Language (DSL)** can be automatically generated from a dataset and used to define and execute a machine‑learning workflow.

Instead of writing complex Python scripts, the system analyzes a dataset and produces a DSL specification that describes the ML workflow. The DSL is then parsed using **textX**, executed using **scikit‑learn**, and exported as a **Common Workflow Language (CWL)** workflow.

This project shows how DSLs can simplify machine‑learning pipelines for domain experts.

---

# System Workflow

```
Dataset Upload
      ↓
Dataset Schema Analysis
      ↓
Automatic DSL Generation
      ↓
DSL Parsing (textX)
      ↓
Machine Learning Pipeline
      ↓
Model Evaluation
      ↓
Prediction Generation
      ↓
CWL Workflow Export
```

---

# Features

• Automatic DSL generation from dataset structure  
• textX‑based DSL grammar and parser  
• Machine learning pipeline (Logistic Regression / Random Forest)  
• Automatic feature detection (numeric / categorical)  
• Evaluation metrics (Accuracy, Precision, Recall, F1, ROC‑AUC)  
• Prediction generation for new cases  
• CWL workflow generation for reproducibility  
• Interactive **Streamlit web interface**  

---

# Project Structure

```
LeadFlowML_EndToEndApp/

app.py
requirements.txt
README.md

src/
    leadflow_common.py

dsl/
    leadflow.tx

data/
    train.csv
    test.csv

outputs/
    model.joblib
    predictions.csv
    report.json
    workflow.cwl

notebooks/
    demo.ipynb
```

---

# Installation

## 1. Clone or Download the Project

Download or clone the repository:

```
git clone <repository-url>
cd LeadFlowML_EndToEndApp
```

---

## 2. Create a Virtual Environment

Mac / Linux

```
python3 -m venv venv
```

Windows

```
python -m venv venv
```

---

## 3. Activate the Environment

Mac / Linux

```
source venv/bin/activate
```

Windows

```
venv\Scripts\activate
```

---

## 4. Install Dependencies

```
pip install -r requirements.txt
```

---

# Running the Application

Start the Streamlit application:

```
streamlit run app.py
```

Then open your browser and go to:

```
http://localhost:8501
```

---

# How to Use the Application

1. Select **Upload my own files**
2. Upload the **training dataset (train.csv)**
3. Upload the **scoring dataset (test.csv)**
4. Click **Auto‑generate DSL from dataset**
5. Review the generated DSL
6. Click **Run end‑to‑end pipeline**

The system will automatically:

• Parse the DSL using **textX**  
• Train the machine‑learning model  
• Evaluate model performance  
• Predict new cases  
• Generate a CWL workflow file  

---

# Example Generated DSL

```
workflow BankMarketingPrediction {

    dataset train_data "train.csv"
    dataset test_data "test.csv"

    target "y"

    numeric "age"
    numeric "balance"
    numeric "duration"
    numeric "campaign"

    categorical "job"
    categorical "marital"
    categorical "education"

    model random_forest
}
```

---

# Dataset

This project demonstrates the workflow using the **Bank Marketing Dataset** from the UCI Machine Learning Repository.

Goal:

Predict whether a client will subscribe to a bank term deposit.

Target column:

```
y (yes / no)
```

Reference:

Moro, S., Cortez, P., & Rita, P. (2014)

*A Data‑Driven Approach to Predict the Success of Bank Telemarketing*

Decision Support Systems.

---

# Generated Outputs

After running the pipeline, the following files are produced:

| File | Description |
|-----|-------------|
| predictions.csv | Model predictions for new cases |
| report.json | Model evaluation metrics |
| model.joblib | Trained machine‑learning model |
| workflow.cwl | Generated CWL workflow |

---

# Technologies Used

Python  
Streamlit  
textX  
Scikit‑learn  
Pandas  
NumPy  
Joblib  

---

# Academic Context

This project was developed for a **Programming Languages / DSL Contest Project**.

The objective was to design and implement a **Domain‑Specific Language capable of automatically defining machine‑learning workflows from datasets**.

---

# Author

Dhruv Patel

Programming Languages Project

Domain‑Specific Languages + Machine Learning Workflow Automation
