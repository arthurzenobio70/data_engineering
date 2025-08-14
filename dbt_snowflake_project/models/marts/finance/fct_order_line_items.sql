{{
  config(
    materialized='table',
    docs={'node_color': 'green'}
  )
}}

with order_items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select * from {{ ref('stg_orders') }}
),

products as (
    select * from {{ ref('stg_products') }}
),

customers as (
    select * from {{ ref('stg_customers') }}
),

final as (
    select
        -- Primary keys
        oi.item_id,
        oi.item_key,
        oi.order_id,
        o.order_key,
        oi.product_id,
        p.product_key,
        o.customer_id,
        c.customer_key,
        
        -- Order information
        o.order_date,
        o.order_status,
        o.order_year,
        o.order_month,
        o.order_day,
        o.order_day_of_week,
        o.is_order_completed,
        o.is_order_cancelled,
        
        -- Customer information
        c.customer_name,
        c.customer_email,
        c.customer_country,
        
        -- Product information
        p.product_name,
        p.product_category,
        p.category_group,
        p.price_segment,
        p.is_high_value as is_high_value_product,
        p.is_electronics,
        
        -- Line item metrics
        oi.quantity,
        oi.unit_price,
        oi.total_price,
        oi.effective_unit_price,
        oi.is_bulk_order,
        oi.price_tier,
        
        -- Calculated metrics
        (oi.unit_price / nullif(p.product_price, 0)) as price_discount_ratio,
        case 
            when p.product_price > 0 then 
                (p.product_price - oi.unit_price) / p.product_price
            else 0
        end as discount_percentage,
        
        -- Revenue allocation
        oi.total_price / nullif(o.total_amount, 0) as line_item_revenue_share,
        
        -- Business classifications
        case 
            when oi.quantity * p.product_price >= 1000 then 'high_value_line'
            when oi.quantity * p.product_price >= 500 then 'medium_value_line'
            else 'low_value_line'
        end as line_item_value_tier,
        
        case 
            when oi.quantity >= 10 then 'bulk_purchase'
            when oi.quantity >= 5 then 'medium_quantity'
            else 'small_quantity'
        end as quantity_tier,
        
        -- Data quality flags
        oi.has_invalid_quantity,
        oi.has_negative_price,
        oi.has_calculation_error,
        o.has_negative_amount as order_has_negative_amount,
        o.has_future_date as order_has_future_date,
        p.has_invalid_price as product_has_invalid_price,
        
        -- Metadata
        oi.dbt_loaded_at,
        current_timestamp as dbt_updated_at
        
    from order_items oi
    left join orders o on oi.order_id = o.order_id
    left join products p on oi.product_id = p.product_id
    left join customers c on o.customer_id = c.customer_id
)

select * from final
