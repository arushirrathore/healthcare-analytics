# Executive Insights Report

**Project:** Hospital Patient Flow & 30-Day Readmission Risk Analysis
**Period analysed:** Jan 2023 - May 2025 (~5,200 admissions)

---

## Headline findings

1. **Cardiology drives readmission cost.** Its 30-day readmission rate runs at roughly **28%, more than double the ~13% rate of General Medicine**, and because Cardiology is also a high-volume, high-cost department, it accounts for the single largest block of estimated readmission spend (SQL query 10).

2. **Age 65+ is a universal risk multiplier.** Across every department, patients 65+ show a consistent uplift of roughly **8 percentage points** in readmission probability. The riskiest single segment is **65+ x Cardiology**.

3. **Winter capacity crunch is predictable.** December-February admissions run **~30-40% above summer levels**, and bed-day demand concentrates in Cardiology and Oncology. This surge repeats every year in the data and is plannable, not random.

4. **Averages hide the worst waits.** In the slowest departments the 90th-percentile wait is roughly **2x the department average**, indicating a triage/process problem rather than pure volume pressure.

5. **Oncology is the cost outlier per case** (avg ~$14.5K per admission), while **Cardiology leads total spend** by combining high per-case cost with high volume.

## Recommendations

| # | Recommendation | Expected impact |
|---|---|---|
| 1 | Launch a 7-day post-discharge call programme for 65+ Cardiology & Oncology patients | Targets the largest readmission cost pool first |
| 2 | Shift to seasonal staffing rosters with a Dec-Feb surge plan | Absorbs the predictable ~35% winter volume uplift |
| 3 | Redesign triage in the two slowest departments, tracking **p90** wait (not average) as the KPI | Directly improves the worst patient experience |
| 4 | Add discharge-planning review for stays >2x department average LOS | Frees bed-days where capacity pressure peaks |
| 5 | Deploy the logistic risk score at discharge to flag high-risk patients | Interpretable triage tool care teams can act on |

## Method note

All figures derive from the cleaned dataset produced by `scripts/clean_data.py` (duplicates removed, kiosk wait-time errors corrected, mixed date formats parsed). The risk model is an intentionally simple logistic regression so coefficients remain explainable to clinical stakeholders.
