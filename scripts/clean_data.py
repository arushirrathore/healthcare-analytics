"""Shared cleaning pipeline for the hospital admissions dataset.

Both the notebooks and the Streamlit dashboard import `clean()` so the
exact same rules apply everywhere -- a single source of truth prevents
the classic \"dashboard disagrees with the notebook\" problem.

Usage:
    python scripts/clean_data.py
Output:
    data/processed/hospital_admissions_clean.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd

RAW_PATH = Path("data/raw/hospital_admissions.csv")
PROCESSED_PATH = Path("data/processed/hospital_admissions_clean.csv")

GENDER_MAP = {"M": "Male", "F": "Female", "Male": "Male", "Female": "Female"}


def parse_mixed_dates(series: pd.Series) -> pd.Series:
    """Handle both ISO (YYYY-MM-DD) and legacy DD/MM/YYYY export formats."""
    iso = pd.to_datetime(series, format="%Y-%m-%d", errors="coerce")
    legacy = pd.to_datetime(series, format="%d/%m/%Y", errors="coerce")
    return iso.fillna(legacy)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all cleaning rules. Each decision is documented inline and
    explained in notebooks/01_data_cleaning.ipynb."""
    df = df.copy()

    # Exact duplicates = double-submitted registration forms -> drop.
    df = df.drop_duplicates()

    # Standardise the four gender encodings produced by the old EHR.
    df["gender"] = df["gender"].map(GENDER_MAP)

    df["admission_date"] = parse_mixed_dates(df["admission_date"])

    # Negative wait times are kiosk export errors -> treat as missing,
    # then impute with the DEPARTMENT median (waits differ a lot by dept,
    # so a global median would bias Emergency vs Oncology).
    df.loc[df["wait_time_minutes"] < 0, "wait_time_minutes"] = np.nan
    df["wait_time_minutes"] = df.groupby("department")["wait_time_minutes"] \
        .transform(lambda s: s.fillna(s.median()))

    # Missing insurance is kept visible as its own category rather than
    # imputed -- billing follow-up needs to know these records exist.
    df["insurance_type"] = df["insurance_type"].fillna("Unknown")

    # Derived analysis columns.
    df["admission_month"] = df["admission_date"].dt.to_period("M").astype(str)
    df["age_group"] = pd.cut(df["age"], [0, 17, 34, 49, 64, 120], right=True,
                             labels=["0-17", "18-34", "35-49", "50-64", "65+"],
                             include_lowest=True)
    df["discharge_date"] = df["admission_date"] + pd.to_timedelta(
        df["length_of_stay_days"], unit="D")
    return df


def main() -> None:
    df = clean(pd.read_csv(RAW_PATH))
    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED_PATH, index=False)
    print(f"Cleaned dataset: {len(df):,} rows -> {PROCESSED_PATH}")


if __name__ == "__main__":
    main()
