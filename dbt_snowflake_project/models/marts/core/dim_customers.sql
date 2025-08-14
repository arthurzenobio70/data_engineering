{{
  config(
    materialized='table',
    docs={'node_color': 'green'}
  )
}}

with customers as (
    select * from {{ ref('stg_customers') }}
),

enriched_orders as (
    select * from {{ ref('int_order_enriched') }}
),

-- Customer order aggregates
customer_metrics as (
    select
        customer_id,
        
        -- Order counts
        count(*) as total_orders,
        count(case when is_order_completed then 1 end) as completed_orders,
        count(case when is_order_cancelled then 1 end) as cancelled_orders,
        
        -- Financial metrics
        sum(reported_total_amount) as lifetime_value,
        avg(reported_total_amount) as avg_order_value,
        max(reported_total_amount) as max_order_value,
        min(reported_total_amount) as min_order_value,
        
        -- Temporal metrics
        min(order_date) as first_order_date,
        max(order_date) as last_order_date,
        max(case when is_order_completed then order_date end) as last_completed_order_date,
        
        -- Product metrics
        sum(item_count) as total_items_purchased,
        sum(unique_product_count) as total_unique_products,
        count(distinct order_value_tier) as order_value_tiers_used,
        
        -- Behavior metrics
        avg(item_count) as avg_items_per_order,
        sum(case when order_size_category = 'large_order' then 1 else 0 end) as large_orders,
        sum(case when has_electronics then 1 else 0 end) as electronics_orders
        
    from enriched_orders
    group by customer_id
),

-- Customer segmentation
customer_segments as (
    select
        customer_id,
        
        -- RFM Analysis components
        case 
            when last_order_date >= current_date - 30 then 5
            when last_order_date >= current_date - 90 then 4
            when last_order_date >= current_date - 180 then 3
            when last_order_date >= current_date - 365 then 2
            else 1
        end as recency_score,
        
        case 
            when total_orders >= 20 then 5
            when total_orders >= 10 then 4
            when total_orders >= 5 then 3
            when total_orders >= 2 then 2
            else 1
        end as frequency_score,
        
        case 
            when lifetime_value >= 5000 then 5
            when lifetime_value >= 2000 then 4
            when lifetime_value >= 1000 then 3
            when lifetime_value >= 500 then 2
            else 1
        end as monetary_score,
        
        -- Business segments
        case 
            when total_orders >= 10 and lifetime_value >= 2000 then 'champion'
            when total_orders >= 5 and lifetime_value >= 1000 then 'loyal_customer'
            when last_order_date >= current_date - 90 and total_orders >= 3 then 'potential_loyalist'
            when last_order_date >= current_date - 30 and total_orders = 1 then 'new_customer'
            when last_order_date < current_date - 180 then 'at_risk'
            when last_order_date < current_date - 365 then 'cannot_lose_them'
            else 'need_attention'
        end as customer_segment
        
    from customer_metrics
),

final as (
    select
        c.customer_id,
        c.customer_key,
        c.customer_name,
        c.customer_email,
        c.customer_country,
        
        -- Order metrics
        coalesce(cm.total_orders, 0) as total_orders,
        coalesce(cm.completed_orders, 0) as completed_orders,
        coalesce(cm.cancelled_orders, 0) as cancelled_orders,
        
        -- Financial metrics
        coalesce(cm.lifetime_value, 0) as lifetime_value,
        coalesce(cm.avg_order_value, 0) as avg_order_value,
        coalesce(cm.max_order_value, 0) as max_order_value,
        coalesce(cm.min_order_value, 0) as min_order_value,
        
        -- Temporal metrics
        cm.first_order_date,
        cm.last_order_date,
        cm.last_completed_order_date,
        
        case 
            when cm.last_order_date is not null 
            then current_date - cm.last_order_date
            else null
        end as days_since_last_order,
        
        case 
            when cm.first_order_date is not null and cm.last_order_date is not null
            then cm.last_order_date - cm.first_order_date
            else null
        end as customer_lifetime_days,
        
        -- Product metrics
        coalesce(cm.total_items_purchased, 0) as total_items_purchased,
        coalesce(cm.total_unique_products, 0) as total_unique_products,
        coalesce(cm.avg_items_per_order, 0) as avg_items_per_order,
        coalesce(cm.large_orders, 0) as large_orders,
        coalesce(cm.electronics_orders, 0) as electronics_orders,
        
        -- Segmentation
        cs.recency_score,
        cs.frequency_score,
        cs.monetary_score,
        cs.customer_segment,
        
        -- Business flags
        case when cm.total_orders >= 5 then true else false end as is_repeat_customer,
        case when cm.last_order_date >= current_date - 90 then true else false end as is_active_customer,
        case when cm.lifetime_value >= 1000 then true else false end as is_high_value_customer,
        case when cm.electronics_orders > 0 then true else false end as has_purchased_electronics,
        
        -- Data quality flags
        c.is_email_missing,
        c.is_name_missing,
        
        -- Metadata
        c.dbt_loaded_at,
        current_timestamp as dbt_updated_at
        
    from customers c
    left join customer_metrics cm on c.customer_id = cm.customer_id
    left join customer_segments cs on c.customer_id = cs.customer_id
)

select * from final
