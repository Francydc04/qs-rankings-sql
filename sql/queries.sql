-- Analytical queries on the QS 2024 database. Each block starts with "-- name: <id>"
-- so src/load.py can run them by name. All queries are standard SQL (SQLite 3.25+ for window functions).

-- name: coverage
-- How much of the ranking has a published overall score?
SELECT
    COUNT(*)                                                    AS universities,
    SUM(overall_score IS NOT NULL)                              AS with_overall_score,
    SUM(rank_2024_min = rank_2024_max)                          AS exact_rank,
    SUM(rank_2024_max IS NULL OR rank_2024_min < rank_2024_max) AS rank_band
FROM Rankings;

-- name: indicator_correlation
-- Pearson correlation of each indicator with the overall score, computed in SQL,
-- over universities that have both values.
WITH pairs AS (
    SELECT 'Academic reputation'   AS indicator, rp.academic_reputation_score   AS x, rk.overall_score AS y FROM Rankings rk JOIN Reputation rp USING (university_id)
    UNION ALL SELECT 'Employer reputation',      rp.employer_reputation_score,     rk.overall_score FROM Rankings rk JOIN Reputation rp USING (university_id)
    UNION ALL SELECT 'Citations per faculty',    rs.citations_per_faculty_score,   rk.overall_score FROM Rankings rk JOIN Research rs USING (university_id)
    UNION ALL SELECT 'International research network', rs.intl_research_network_score, rk.overall_score FROM Rankings rk JOIN Research rs USING (university_id)
    UNION ALL SELECT 'Faculty/student ratio',    fs.faculty_student_score,         rk.overall_score FROM Rankings rk JOIN FacultyStudents fs USING (university_id)
    UNION ALL SELECT 'International faculty',    fs.intl_faculty_score,            rk.overall_score FROM Rankings rk JOIN FacultyStudents fs USING (university_id)
    UNION ALL SELECT 'International students',   fs.intl_student_score,            rk.overall_score FROM Rankings rk JOIN FacultyStudents fs USING (university_id)
    UNION ALL SELECT 'Employment outcomes',      eo.employment_outcomes_score,     rk.overall_score FROM Rankings rk JOIN EmploymentOutcomes eo USING (university_id)
    UNION ALL SELECT 'Sustainability',           su.sustainability_score,          rk.overall_score FROM Rankings rk JOIN Sustainability su USING (university_id)
),
clean AS (SELECT * FROM pairs WHERE x IS NOT NULL AND y IS NOT NULL)
SELECT
    indicator,
    COUNT(*) AS n,
    ROUND((COUNT(*) * SUM(x * y) - SUM(x) * SUM(y)) /
          (SQRT(COUNT(*) * SUM(x * x) - SUM(x) * SUM(x)) * SQRT(COUNT(*) * SUM(y * y) - SUM(y) * SUM(y))), 3) AS pearson_r
FROM clean
GROUP BY indicator
ORDER BY pearson_r DESC;

-- name: country_concentration
-- Where are the top universities? Countries ranked by universities in the top 100.
SELECT
    c.country_name,
    SUM(rk.rank_2024_max <= 100)  AS top_100,
    SUM(rk.rank_2024_max <= 500)  AS top_500,
    COUNT(*)                      AS ranked
FROM University u
JOIN Country c   USING (country_code)
JOIN Rankings rk USING (university_id)
GROUP BY c.country_name
HAVING top_100 > 0
ORDER BY top_100 DESC, top_500 DESC
LIMIT 12;

-- name: best_by_country
-- Highest-ranked university in each of the 12 countries with most ranked universities (window function).
WITH ranked AS (
    SELECT c.country_name, u.institution_name, rk.rank_2024_label, rk.rank_2024_min,
           RANK()   OVER (PARTITION BY c.country_code ORDER BY rk.rank_2024_min) AS position_in_country,
           COUNT(*) OVER (PARTITION BY c.country_code)                           AS universities_in_country
    FROM University u
    JOIN Country c   USING (country_code)
    JOIN Rankings rk USING (university_id)
)
SELECT country_name, institution_name AS best_university, rank_2024_label AS world_rank, universities_in_country
FROM ranked
WHERE position_in_country = 1
ORDER BY universities_in_country DESC
LIMIT 12;

-- name: employability_gap
-- Universities whose employer reputation far exceeds their academic reputation:
-- valued by recruiters more than by academics. Restricted to the top 500.
SELECT
    u.institution_name,
    c.country_name,
    rk.rank_2024_label                                          AS world_rank,
    rp.academic_reputation_score                                AS academic_rep,
    rp.employer_reputation_score                                AS employer_rep,
    ROUND(rp.employer_reputation_score - rp.academic_reputation_score, 1) AS gap
FROM University u
JOIN Country c    USING (country_code)
JOIN Rankings rk  USING (university_id)
JOIN Reputation rp USING (university_id)
WHERE rk.rank_2024_max <= 500
ORDER BY gap DESC
LIMIT 10;

-- name: employment_by_country
-- Average employment-outcomes score by country, only for countries with at least 20 ranked universities
-- (averages over one or two institutions are not comparable).
SELECT
    c.country_name,
    COUNT(eo.employment_outcomes_score)            AS universities,
    ROUND(AVG(eo.employment_outcomes_score), 1)    AS avg_employment_outcomes,
    ROUND(AVG(rp.employer_reputation_score), 1)    AS avg_employer_reputation
FROM University u
JOIN Country c             USING (country_code)
JOIN EmploymentOutcomes eo USING (university_id)
JOIN Reputation rp         USING (university_id)
GROUP BY c.country_name
HAVING COUNT(eo.employment_outcomes_score) >= 20
ORDER BY avg_employment_outcomes DESC;

-- name: biggest_movers
-- Largest moves between 2023 and 2024 among universities with exact ranks in both years and a 2024 top-200 place.
SELECT
    u.institution_name,
    c.country_name,
    rk.rank_2023_min                    AS rank_2023,
    rk.rank_2024_min                    AS rank_2024,
    rk.rank_2023_min - rk.rank_2024_min AS places_gained
FROM University u
JOIN Country c   USING (country_code)
JOIN Rankings rk USING (university_id)
WHERE rk.rank_2024_max <= 200
  AND rk.rank_2023_min IS NOT NULL
  AND rk.rank_2023_label NOT LIKE '%-%' AND rk.rank_2023_label NOT LIKE '%+%'
ORDER BY ABS(rk.rank_2023_min - rk.rank_2024_min) DESC
LIMIT 10;

-- name: zero_fill_bias
-- Why missing values must stay NULL: the original loader replaced them with 0.
SELECT
    ROUND(AVG(overall_score), 1)                       AS avg_overall_score_null_kept,
    ROUND(AVG(COALESCE(overall_score, 0)), 1)          AS avg_overall_score_zero_filled,
    ROUND(AVG(e.employment_outcomes_score), 1)         AS avg_employment_null_kept,
    ROUND(AVG(COALESCE(e.employment_outcomes_score, 0)), 1) AS avg_employment_zero_filled
FROM Rankings
JOIN EmploymentOutcomes e USING (university_id);
