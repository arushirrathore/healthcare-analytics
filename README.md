# 🏥 Hospital Patient Flow & Readmission Risk Analysis

![Python](https://img.shields.io/badge/Python-3.11-blue) ![Pandas](https://img.shields.io/badge/Pandas-2.2-150458) ![SQL](https://img.shields.io/badge/SQL-SQLite-orange) ![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B) ![scikit--learn](https://img.shields.io/badge/ML-scikit--learn-F7931E)

An end-to-end **healthcare analytics** project: from a messy raw hospital export to a cleaned dataset, SQL analysis, statistical deep-dives, an interpretable readmission risk score, and an interactive operations dashboard.

---

## 📋 Business problem

A mid-size hospital faces three linked operational questions:

1. **Readmissions:** which departments and patient cohorts drive avoidable 30-day readmissions, and what do they cost?
2. **Capacity:** how seasonal is admission demand, and where does bed-day pressure concentrate?
3. **Patient experience:** where are wait times worst, and is it a volume problem or a process problem?

## 📊 Dataset

~5,200 synthetic admission records (Jan 2023 - May 2025) generated with realistic statistical structure: department case mix, winter admission surges, age-driven readmission risk, log-normal cost distributions. Real patient data is protected (HIPAA/DPDP), so the generator recreates the patterns **and the mess**: duplicate registrations, mixed date formats, inconsistent gender encodings, missing values and impossible (negative) wait times - all handled in a documented cleaning pipeline.

## 🔍 Key insights

- **Cardiology shows a ~28% 30-day readmission rate vs a ~16% hospital average** - and being high-volume + high-cost, it is the largest readmission cost pool.
- **Age 65+ adds ~8 percentage points of readmission risk in every department**; the 65+ x Cardiology cohort is the single riskiest segment.
- **Winter admissions run ~30-40% above summer**, with bed-day pressure concentrated in Cardiology and Oncology.
- **P90 waits are ~2x the average** in the slowest departments - a triage/process issue, not just volume.
- An interpretable **logistic regression risk score** confirms department and age as dominant drivers and provides a usable discharge-triage tool.

Full business-style write-up: [`docs/INSIGHTS.md`](docs/INSIGHTS.md)

## 🗂️ Project structure

```
├── data/
│   ├── raw/         # generated raw export (gitignored)
│   └── processed/   # cleaned dataset (gitignored)
├── scripts/
│   ├── generate_data.py   # synthetic data generator (seeded, reproducible)
│   └── clean_data.py      # shared cleaning pipeline (single source of truth)
├── sql/
│   └── analysis_queries.sql  # 10 commented analysis queries (SQLite)
├── notebooks/
│   ├── 01_data_cleaning.ipynb        # audit + documented cleaning decisions
│   ├── 02_exploratory_analysis.ipynb # seasonality, waits, cost, bed-days
│   └── 03_readmission_analysis.ipynb # cohorts + logistic risk score
├── dashboard/
│   └── app.py       # interactive Streamlit + Plotly dashboard
└── docs/
    └── INSIGHTS.md  # executive summary & recommendations
```

## 🚀 How to run

```bash
# 1. Setup
git clone https://gitlab.com/vikashcode-group/healthcare-analytics.git
cd healthcare-analytics
pip install -r requirements.txt

# 2. Generate the raw dataset (seeded - fully reproducible)
python scripts/generate_data.py

# 3. Run the cleaning pipeline
python scripts/clean_data.py

# 4. Explore the notebooks
jupyter notebook notebooks/

# 5. Launch the dashboard
streamlit run dashboard/app.py
```

For the SQL analysis, load the cleaned CSV into SQLite:

```bash
sqlite3 hospital.db
.mode csv
.import data/processed/hospital_admissions_clean.csv admissions
.read sql/analysis_queries.sql
```

## 📸 Dashboard preview

> _Add a screenshot here after running the dashboard:_ `docs/dashboard_screenshot.png`

The dashboard includes KPI cards (wait time, readmission rate, LOS, cost), department/date filters, admission trend lines, a readmission heatmap by department x age group, wait-time p90 comparison and revenue mix - all interactive via Plotly.

## 🛠️ Tech stack

**Python** (pandas, NumPy) - **SQL** (SQLite) - **matplotlib / seaborn** - **Plotly + Streamlit** - **scikit-learn** - **Jupyter**

## 📝 Methodology highlights

- Every cleaning decision is **documented with rationale** in notebook 01 (e.g., department-median imputation for wait times instead of a biased global median).
- Notebooks and dashboard share **one cleaning module** (`scripts/clean_data.py`) so numbers never disagree.
- The risk model is **deliberately interpretable** - clinical stakeholders need readable coefficients, not a black box.
