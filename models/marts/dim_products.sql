{{ config(
    materialized='table',
    schema='MARTS'
) }}

WITH stg_sales AS (
    SELECT * FROM {{ ref('stg_banhang') }}
),

ranked AS (
    SELECT
        product_id,
        product_name,
        category_path,
        ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY transaction_at DESC) AS rn
    FROM stg_sales
    WHERE product_id IS NOT NULL
)

SELECT
    MD5(product_id) AS product_key,
    product_id,
    product_name,
    category_path
FROM ranked
WHERE rn = 1
