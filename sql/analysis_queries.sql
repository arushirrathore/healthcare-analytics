-- ====================================================================
-- Hospital Analytics: core analysis queries (SQLite-compatible)
--
-- Load the cleaned CSV into SQLite first:
--   sqlite3 hospital.db
--   .mode csv
--   .import data/processed/hospital_admissions_clean.csv admissions
-- ====================================================================

-- 1. 30-day readmission rate by department vs hospital average
--    (the headline metric: which departments drive readmission cost?)
SELECT department,
       COUNT(*)                            AS admissions,
       ROUND(AVG(readmitted_30d) * 100, 1) AS readmission_rate_pct,
       ROUND((SELECT AVG(readmitted_30d) * 100 FROM admissions), 1)
                                           AS hospital_avg_pct
FROM admissions
GROUP BY department
ORDER BY readmission_rate_pct DESC;

-- 2. Average and 90th-percentile wait time by department
--    (averages hide the worst patient experience; p90 exposes it)
SELECT department,
       ROUND(AVG(wait_time_minutes), 1) AS avg_wait_min,
       (SELECT wait_time_minutes FROM admissions a2
        WHERE a2.department = a1.department
        ORDER BY wait_time_minutes
        LIMIT 1 OFFSET CAST(0.9 * (SELECT COUNT(*) FROM admissions a3
                                   WHERE a3.department = a1.department) AS INT)
       ) AS p90_wait_min
FROM admissions a1
GROUP BY department
ORDER BY avg_wait_min DESC;

-- 3. Monthly admission seasonality (capacity planning input)
SELECT admission_month,
       COUNT(*)                              AS admissions,
       ROUND(AVG(length_of_stay_days), 1)    AS avg_los_days
FROM admissions
GROUP BY admission_month
ORDER BY admission_month;

-- 4. Bed-day demand by month (occupancy proxy: total bed-days consumed)
SELECT admission_month,
       ROUND(SUM(length_of_stay_days), 0) AS bed_days_consumed
FROM admissions
GROUP BY admission_month
ORDER BY bed_days_consumed DESC;

-- 5. High-risk cohort: patients 65+ in high-readmission departments
SELECT department, COUNT(*) AS patients_65_plus,
       ROUND(AVG(readmitted_30d) * 100, 1) AS readmission_rate_pct,
       ROUND(AVG(treatment_cost), 0)       AS avg_cost
FROM admissions
WHERE age >= 65
GROUP BY department
HAVING AVG(readmitted_30d) > (SELECT AVG(readmitted_30d) FROM admissions)
ORDER BY readmission_rate_pct DESC;

-- 6. Treatment cost by insurance type (revenue mix analysis)
SELECT insurance_type,
       COUNT(*)                         AS admissions,
       ROUND(AVG(treatment_cost), 0)    AS avg_cost,
       ROUND(SUM(treatment_cost), 0)    AS total_revenue
FROM admissions
GROUP BY insurance_type
ORDER BY total_revenue DESC;

-- 7. Top 10 most expensive diagnoses (cost-control targets)
SELECT diagnosis, department,
       COUNT(*)                      AS cases,
       ROUND(AVG(treatment_cost), 0) AS avg_cost,
       ROUND(SUM(treatment_cost), 0) AS total_cost
FROM admissions
GROUP BY diagnosis, department
ORDER BY total_cost DESC
LIMIT 10;

-- 8. Length-of-stay outliers: stays > 2x the department average
SELECT a.patient_id, a.department, a.diagnosis,
       a.length_of_stay_days,
       ROUND(d.dept_avg, 1) AS dept_avg_los
FROM admissions a
JOIN (SELECT department, AVG(length_of_stay_days) AS dept_avg
      FROM admissions GROUP BY department) d
  ON a.department = d.department
WHERE a.length_of_stay_days > 2 * d.dept_avg
ORDER BY a.length_of_stay_days DESC;

-- 9. Readmission rate by age group (clinical risk stratification)
SELECT age_group,
       COUNT(*)                            AS admissions,
       ROUND(AVG(readmitted_30d) * 100, 1) AS readmission_rate_pct
FROM admissions
GROUP BY age_group
ORDER BY readmission_rate_pct DESC;

-- 10. Estimated annual cost of readmissions by department
--     (rate x volume x avg cost = the business case for intervention)
SELECT department,
       SUM(readmitted_30d)                                   AS readmissions,
       ROUND(SUM(readmitted_30d) * AVG(treatment_cost), 0)   AS est_readmission_cost
FROM admissions
GROUP BY department
ORDER BY est_readmission_cost DESC;
