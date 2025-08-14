-- Singular test to reconcile revenue between different models
-- Ensures consistency across staging and marts layers

{{ config(tags=['business_logic']) }}

with staging_revenue as (
    select
        date_trunc('day', order_date) as order_date,
        sum(total_amount) as staging_total_revenue
    from {{ ref('stg_orders') }}
    where is_order_completed = true
    group by date_trunc('day', order_date)
),

marts_revenue as (
    select
        order_date,
        sum(completed_revenue) as marts_total_revenue
    from {{ ref('fct_daily_order_revenue') }}
    group by order_date
),

revenue_comparison as (
    select
        coalesce(s.order_date, m.order_date) as order_date,
        coalesce(s.staging_total_revenue, 0) as staging_revenue,
        coalesce(m.marts_total_revenue, 0) as marts_revenue,
        abs(coalesce(s.staging_total_revenue, 0) - coalesce(m.marts_total_revenue, 0)) as difference
    from staging_revenue s
    full outer join marts_revenue m on s.order_date = m.order_date
)

select *
from revenue_comparison
where difference > 0.01  -- Allow for small rounding differences
