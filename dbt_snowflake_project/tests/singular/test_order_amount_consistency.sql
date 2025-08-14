-- Singular test to check order amount consistency
-- between orders and calculated order items total

{{ config(tags=['data_integrity']) }}

with order_totals as (
    select
        o.order_id,
        o.total_amount as reported_amount,
        sum(oi.total_price) as calculated_amount,
        abs(o.total_amount - sum(oi.total_price)) as difference
    from {{ ref('stg_orders') }} o
    left join {{ ref('stg_order_items') }} oi on o.order_id = oi.order_id
    group by o.order_id, o.total_amount
)

select *
from order_totals
where difference > 0.01  -- Allow for small rounding differences
