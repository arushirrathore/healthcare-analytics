"""Synthetic hospital admissions dataset generator.

Why synthetic? Real patient data is protected (HIPAA / DPDP Act). This
script recreates the statistical fingerprints of a mid-size hospital --
department case mix, winter admission surges, age-driven readmission
risk -- while injecting realistic data-quality problems (missing values,
duplicate rows, inconsistent encodings) so the downstream cleaning
pipeline demonstrates real analyst work, not cosmetic steps.

Usage:
    python scripts/generate_data.py
Output:
    data/raw/hospital_admissions.csv  (~5,260 rows)
"""

from pathlib import Path

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
N_RECORDS = 5200
OUTPUT_PATH = Path("data/raw/hospital_admissions.csv")

# Department profiles: admission share, avg length of stay (days),
# baseline 30-day readmission probability, avg treatment cost (USD).
DEPARTMENTS = {
    "Cardiology":       {"share": 0.18, "los": 6.5, "readmit": 0.28, "cost": 9500},
    "General Medicine": {"share": 0.22, "los": 4.0, "readmit": 0.13, "cost": 4100},
    "Orthopedics":      {"share": 0.14, "los": 5.0, "readmit": 0.11, "cost": 8200},
    "Emergency":        {"share": 0.15, "los": 1.5, "readmit": 0.16, "cost": 2800},
    "Pediatrics":       {"share": 0.12, "los": 3.0, "readmit": 0.07, "cost": 3500},
    "Neurology":        {"share": 0.10, "los": 6.0, "readmit": 0.18, "cost": 10800},
    "Oncology":         {"share": 0.09, "los": 8.5, "readmit": 0.24, "cost": 14500},
}

DIAGNOSES = {
    "Cardiology": ["Heart Failure", "Arrhythmia", "Myocardial Infarction"],
    "General Medicine": ["Diabetes Complications", "Pneumonia", "Hypertension Crisis"],
    "Orthopedics": ["Hip Replacement", "Fracture", "Spinal Surgery"],
    "Emergency": ["Trauma", "Acute Abdominal Pain", "Respiratory Distress"],
    "Pediatrics": ["Bronchiolitis", "Gastroenteritis", "Asthma"],
    "Neurology": ["Stroke", "Epilepsy", "Severe Migraine"],
    "Oncology": ["Chemotherapy Cycle", "Tumor Resection", "Radiation Therapy"],
}

INSURANCE = ["Private", "Government", "Self-Pay"]


def seasonal_dates(n: int) -> pd.Series:
    """Sample admission dates (2023-01 to 2025-05) with a winter surge.

    Respiratory and cardiac admissions peak Dec-Feb in most hospitals,
    so winter months get ~40% more weight; mid-summer dips slightly.
    """
    days = pd.date_range("2023-01-01", "2025-05-31", freq="D")
    weight = np.where(np.isin(days.month, [12, 1, 2]), 1.4,
             np.where(np.isin(days.month, [6, 7]), 0.85, 1.0))
    return pd.Series(RNG.choice(days, size=n, p=weight / weight.sum()))


def build_dataset() -> pd.DataFrame:
    depts = RNG.choice(list(DEPARTMENTS), size=N_RECORDS,
                       p=[d["share"] for d in DEPARTMENTS.values()])
    profile = pd.DataFrame([DEPARTMENTS[d] for d in depts])

    # Age skews older for cardiac/oncology patients, younger for pediatrics.
    base_age = RNG.normal(52, 18, N_RECORDS).clip(0, 95)
    age = np.where(depts == "Pediatrics", RNG.integers(0, 16, N_RECORDS),
          np.where(np.isin(depts, ["Cardiology", "Oncology"]),
                   (base_age + 12).clip(18, 95), base_age)).astype(int)

    los = np.maximum(RNG.gamma(2.0, profile["los"] / 2.0), 0.25)

    # Readmission risk = department baseline + age effect (65+ adds ~8 pts).
    readmit_p = (profile["readmit"] + np.where(age >= 65, 0.08, 0.0)).clip(0, 0.9)

    return pd.DataFrame({
        "patient_id": [f"PT{100000 + i}" for i in range(N_RECORDS)],
        "age": age,
        "gender": RNG.choice(["Male", "Female"], N_RECORDS),
        "department": depts,
        "diagnosis": [RNG.choice(DIAGNOSES[d]) for d in depts],
        "admission_date": seasonal_dates(N_RECORDS).dt.strftime("%Y-%m-%d"),
        "length_of_stay_days": los.round(1),
        "wait_time_minutes": RNG.gamma(2.2, 22, N_RECORDS).round(0),
        "treatment_cost": (profile["cost"] * RNG.lognormal(0, 0.35, N_RECORDS)).round(2),
        "insurance_type": RNG.choice(INSURANCE, N_RECORDS, p=[0.45, 0.40, 0.15]),
        "readmitted_30d": (RNG.random(N_RECORDS) < readmit_p).astype(int),
        "bed_id": [f"B-{RNG.integers(1, 320):03d}" for _ in range(N_RECORDS)],
    })


def inject_quality_issues(df: pd.DataFrame) -> pd.DataFrame:
    """Add realistic mess so the cleaning notebook has genuine work to do."""
    df = df.copy()

    # 1. Inconsistent gender encodings (~12% exported as M/F by old EHR).
    idx = RNG.choice(df.index, int(0.12 * len(df)), replace=False)
    df.loc[idx, "gender"] = df.loc[idx, "gender"].map({"Male": "M", "Female": "F"})

    # 2. Missing values: wait times (~4%) and insurance type (~3%).
    df.loc[RNG.choice(df.index, int(0.04 * len(df)), replace=False),
           "wait_time_minutes"] = np.nan
    df.loc[RNG.choice(df.index, int(0.03 * len(df)), replace=False),
           "insurance_type"] = np.nan

    # 3. Impossible values: negative wait times from a faulty kiosk export.
    idx = RNG.choice(df.index, 35, replace=False)
    df.loc[idx, "wait_time_minutes"] = -df.loc[idx, "wait_time_minutes"].abs()

    # 4. Mixed date formats (~8% exported as DD/MM/YYYY by a legacy system).
    idx = RNG.choice(df.index, int(0.08 * len(df)), replace=False)
    df.loc[idx, "admission_date"] = pd.to_datetime(
        df.loc[idx, "admission_date"]).dt.strftime("%d/%m/%Y")

    # 5. Duplicate rows (double-submitted registration forms).
    return pd.concat([df, df.sample(60, random_state=42)], ignore_index=True)


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df = inject_quality_issues(build_dataset())
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {len(df):,} rows -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
