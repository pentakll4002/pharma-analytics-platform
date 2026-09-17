{{ config(
    materialized='view',
    schema='INTERMEDIATE'
) }}

WITH stg_sales AS (
    SELECT * FROM {{ ref('stg_banhang') }}
)

SELECT
    transaction_id,
    branch_name,
    transaction_at,
    period_month,
    COUNT(product_id) AS total_distinct_items,
    SUM(quantity) AS total_quantity,
    SUM(item_revenue) AS total_transaction_revenue,
    SUM(gross_profit) AS total_transaction_profit
FROM stg_sales
GROUP BY transaction_id, branch_name, transaction_at, period_month
