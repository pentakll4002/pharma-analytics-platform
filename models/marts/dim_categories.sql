{{ config(
    materialized='table',
    schema='MARTS'
) }}

WITH stg_sales AS (
    SELECT * FROM {{ ref('stg_banhang') }}
)

SELECT DISTINCT
    MD5(category_path) AS category_key,
    category_path
FROM stg_sales
WHERE category_path IS NOT NULL
