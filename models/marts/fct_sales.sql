{{ config(
    materialized='table',
    schema='MARTS'
) }}

WITH stg_sales AS (
    SELECT * FROM {{ ref('stg_banhang') }}
),
dim_branches AS (
    SELECT * FROM {{ ref('dim_branches') }}
),
dim_products AS (
    SELECT * FROM {{ ref('dim_products') }}
),
dim_date AS (
    SELECT * FROM {{ ref('dim_date') }}
),
dim_categories AS (
    SELECT * FROM {{ ref('dim_categories') }}
)

SELECT
    s.transaction_id,
    s.transaction_at,
    d.date_key,
    b.branch_key,
    c.category_key,
    c.category_path,
    s.branch_name,
    p.product_key,
    s.product_id,
    s.product_name,
    s.quantity,
    s.unit_price,
    s.unit_cost,
    s.item_revenue,
    s.gross_profit,
    s.period_month
FROM stg_sales s
LEFT JOIN dim_branches b ON s.branch_name = b.branch_name
LEFT JOIN dim_products p ON s.product_id = p.product_id
LEFT JOIN dim_date d ON s.transaction_at::DATE = d.date_day
LEFT JOIN dim_categories c ON s.category_path = c.category_path
