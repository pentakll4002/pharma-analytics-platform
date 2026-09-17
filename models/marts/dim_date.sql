{{ config(
    materialized='table',
    schema='MARTS'
) }}

WITH stg_sales AS (
    SELECT * FROM {{ ref('stg_banhang') }}
),

distinct_dates AS (
    SELECT DISTINCT
        transaction_at::DATE AS date_day
    FROM stg_sales
    WHERE transaction_at IS NOT NULL
)

SELECT
    MD5(date_day::VARCHAR) AS date_key,
    date_day,
    YEAR(date_day)                              AS year,
    MONTH(date_day)                             AS month,
    DAY(date_day)                               AS day,
    QUARTER(date_day)                           AS quarter,
    DAYOFWEEK(date_day)                         AS day_of_week,
    DAYNAME(date_day)                           AS day_name,
    MONTHNAME(date_day)                         AS month_name,
    WEEKOFYEAR(date_day)                        AS week_of_year,
    CASE WHEN DAYOFWEEK(date_day) IN (0, 6)
         THEN TRUE ELSE FALSE END               AS is_weekend
FROM distinct_dates
