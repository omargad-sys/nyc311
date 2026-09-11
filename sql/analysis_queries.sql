-- NYC311 Pulse: example analytical queries

-- 1. Average resolution time by agency, ranked worst to best.
--    Uses a CTE plus RANK() window function.
WITH agency_resolution AS (
    SELECT
        a.agency_name,
        AVG(f.resolution_hours) AS avg_resolution_hours,
        COUNT(*) AS request_count
    FROM fact_311_requests f
    JOIN dim_agency a ON a.agency_code = f.agency_code
    WHERE f.resolution_hours IS NOT NULL
    GROUP BY a.agency_name
    HAVING COUNT(*) >= 100
)
SELECT
    agency_name,
    ROUND(avg_resolution_hours, 1) AS avg_resolution_hours,
    request_count,
    RANK() OVER (ORDER BY avg_resolution_hours DESC) AS slowest_rank
FROM agency_resolution
ORDER BY slowest_rank;


-- 2. Month over month change in complaint volume.
--    Uses LAG() to compare each month to the one before it.
WITH monthly_volume AS (
    SELECT
        DATE_TRUNC('month', created_date_key) AS month,
        COUNT(*) AS request_count
    FROM fact_311_requests
    GROUP BY DATE_TRUNC('month', created_date_key)
)
SELECT
    month,
    request_count,
    LAG(request_count) OVER (ORDER BY month) AS prior_month_count,
    ROUND(
        100.0 * (request_count - LAG(request_count) OVER (ORDER BY month))
        / NULLIF(LAG(request_count) OVER (ORDER BY month), 0)
    , 1) AS pct_change
FROM monthly_volume
ORDER BY month;


-- 3. Top 3 complaint types per borough.
--    Uses ROW_NUMBER() partitioned by borough.
WITH complaint_counts AS (
    SELECT
        borough,
        complaint_type,
        COUNT(*) AS request_count
    FROM fact_311_requests
    WHERE borough IS NOT NULL
    GROUP BY borough, complaint_type
),
ranked AS (
    SELECT
        borough,
        complaint_type,
        request_count,
        ROW_NUMBER() OVER (PARTITION BY borough ORDER BY request_count DESC) AS rn
    FROM complaint_counts
)
SELECT borough, complaint_type, request_count
FROM ranked
WHERE rn <= 3
ORDER BY borough, rn;


-- 4. SLA compliance: share of requests each agency closed within 3 days.
WITH sla_flagged AS (
    SELECT
        a.agency_name,
        f.unique_key,
        CASE WHEN f.resolution_hours <= 72 THEN 1 ELSE 0 END AS closed_within_sla
    FROM fact_311_requests f
    JOIN dim_agency a ON a.agency_code = f.agency_code
    WHERE f.resolution_hours IS NOT NULL
)
SELECT
    agency_name,
    COUNT(*) AS total_closed,
    SUM(closed_within_sla) AS closed_within_3_days,
    ROUND(100.0 * SUM(closed_within_sla) / COUNT(*), 1) AS sla_compliance_pct
FROM sla_flagged
GROUP BY agency_name
HAVING COUNT(*) >= 100
ORDER BY sla_compliance_pct ASC;
