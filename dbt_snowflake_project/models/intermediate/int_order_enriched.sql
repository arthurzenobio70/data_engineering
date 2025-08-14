{{
  config(
    materialized='view',
    docs={'node_color': 'orange'}
  )
}}

with orders as (
    select * from {{ ref('stg_orders') }}
),

customers as (
    select * from {{ ref('stg_customers') }}
),

order_items as (
    select * from {{ ref('stg_order_items') }}
),

products as (
    select * from {{ ref('stg_products') }}
),

-- Aggregate order items to order level
order_aggregates as (
    select
        order_id,
        count(*) as item_count,
        sum(quantity) as total_quantity,
        sum(total_price) as calculated_total_amount,
        avg(unit_price) as avg_unit_price,
        max(unit_price) as max_unit_price,
        min(unit_price) as min_unit_price,
        count(distinct product_id) as unique_product_count,
        sum(case when is_bulk_order then 1 else 0 end) as bulk_item_count,
        
        -- Product category distribution
        count(distinct p.product_category) as unique_categories,
        max(case when p.is_electronics then 1 else 0 end) as has_electronics
        
    from order_items oi
    left join products p on oi.product_id = p.product_id
    group by order_id
),

-- Join all components
enriched_orders as (
    select
        o.order_id,
        o.order_key,
        o.customer_id,
        o.order_date,
        o.total_amount as reported_total_amount,
        o.order_status,
        o.order_year,
        o.order_month,
        o.order_day,
        o.order_day_of_week,
        o.is_order_completed,
        o.is_order_cancelled,
        o.is_recent_order,
        
        -- Customer information
        c.customer_name,
        c.customer_email,
        c.customer_country,
        c.is_email_missing,
        c.is_name_missing,
        
        -- Order aggregates
        oa.item_count,
        oa.total_quantity,
        oa.calculated_total_amount,
        oa.avg_unit_price,
        oa.max_unit_price,
        oa.min_unit_price,
        oa.unique_product_count,
        oa.bulk_item_count,
        oa.unique_categories,
        oa.has_electronics,
        
        -- Business metrics
        case 
            when oa.item_count = 1 then 'single_item'
            when oa.item_count <= 5 then 'small_order'
            when oa.item_count <= 15 then 'medium_order'
            else 'large_order'
        end as order_size_category,
        
        case 
            when o.total_amount < 50 then 'low_value'
            when o.total_amount < 200 then 'medium_value'
            when o.total_amount < 1000 then 'high_value'
            else 'very_high_value'
        end as order_value_tier,
        
        -- Data quality flags
        case 
            when abs(o.total_amount - oa.calculated_total_amount) > 0.01 then true
            else false
        end as has_amount_discrepancy,
        
        o.has_negative_amount,
        o.has_future_date,
        
        -- Metadata
        o.dbt_loaded_at,
        o.dbt_updated_at
        
    from orders o
    left join customers c on o.customer_id = c.customer_id
    left join order_aggregates oa on o.order_id = oa.order_id
)

select * from enriched_orders
