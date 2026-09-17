{{ config(
    materialized='view',
    schema='STAGING'
) }}

SELECT
    MA_GIAO_DICH                                AS transaction_id,
    CHI_NHANH                                   AS branch_name,
    TRY_TO_TIMESTAMP_NTZ(THOI_GIAN_GIAO_DICH)  AS transaction_at,
    MA_HANG                                     AS product_id,
    TRIM(TEN_HANG)                              AS product_name,
    TRIM(NHOM_HANG)                             AS category_path,
    CAST(SO_LUONG AS FLOAT)                     AS quantity,
    CAST(GIA_BAN_SP AS FLOAT)                   AS unit_price,
    CAST(DOANH_THU AS FLOAT)                    AS item_revenue,
    CAST(GIA_VON_SP AS FLOAT)                   AS unit_cost,
    CAST(TONG_TIEN_HANG AS FLOAT)               AS gross_amount,
    CAST(DOANH_THU_GIAO_DICH AS FLOAT)          AS net_revenue,
    CAST(TONG_GIA_VON AS FLOAT)                 AS total_cost,
    CAST(LOI_NHUAN_GOP AS FLOAT)                AS gross_profit,
    THOI_GIAN                                   AS period_month
FROM {{ source('raw_data', 'BANHANG') }}