{{ config(
    materialized='table',
    schema='MARTS'
) }}

WITH stg_sales AS (
    SELECT * FROM {{ ref('stg_banhang') }}
)

SELECT DISTINCT
    MD5(branch_name) AS branch_key,
    branch_name
FROM stg_sales
WHERE branch_name IS NOT NULL
