{{
  config(
    materialized='table',
    docs={'node_color': 'green'},
    indexes=[
      {'columns': ['order_date'], 'type': 'btree'},
      {'columns': ['order_date', 'customer_country'], 'type': 'btree'}
    ]
  )
}}

with enriched_orders as (
    select * from {{ ref('int_order_enriched') }}
),

daily_metrics as (
    select
        order_date,
        customer_country,
        order_status,
        order_value_tier,
        order_size_category,
        
        -- Order counts
        count(*) as total_orders,
        count(case when is_order_completed then 1 end) as completed_orders,
        count(case when is_order_cancelled then 1 end) as cancelled_orders,
        count(case when order_status = 'PENDING' then 1 end) as pending_orders,
        
        -- Revenue metrics
        sum(reported_total_amount) as total_revenue,
        sum(case when is_order_completed then reported_total_amount else 0 end) as completed_revenue,
        avg(reported_total_amount) as avg_order_value,
        median(reported_total_amount) as median_order_value,
        min(reported_total_amount) as min_order_value,
        max(reported_total_amount) as max_order_value,
        
        -- Customer metrics
        count(distinct customer_id) as unique_customers,
        sum(case when is_recent_order then 1 else 0 end) as recent_orders,
        
        -- Product metrics
        sum(item_count) as total_items_sold,
        sum(unique_product_count) as total_unique_products,
        sum(bulk_item_count) as total_bulk_items,
        avg(unique_categories) as avg_categories_per_order,
        
        -- Quality flags
        sum(case when has_amount_discrepancy then 1 else 0 end) as orders_with_discrepancy,
        sum(case when has_future_date then 1 else 0 end) as orders_with_future_date,
        sum(case when has_negative_amount then 1 else 0 end) as orders_with_negative_amount
        
    from enriched_orders
    where order_date is not null
    group by 
        order_date,
        customer_country,
        order_status,
        order_value_tier,
        order_size_category
),

-- Add derived metrics
final as (
    select
        order_date,
        customer_country,
        order_status,
        order_value_tier,
        order_size_category,
        
        -- Core metrics
        total_orders,
        completed_orders,
        cancelled_orders,
        pending_orders,
        unique_customers,
        
        -- Revenue metrics
        total_revenue,
        completed_revenue,
        avg_order_value,
        median_order_value,
        min_order_value,
        max_order_value,
        
        -- Product metrics
        total_items_sold,
        total_unique_products,
        total_bulk_items,
        avg_categories_per_order,
        
        -- Calculated ratios
        case 
            when total_orders > 0 then completed_orders::float / total_orders::float
            else 0
        end as completion_rate,
        
        case 
            when total_orders > 0 then cancelled_orders::float / total_orders::float
            else 0
        end as cancellation_rate,
        
        case 
            when total_items_sold > 0 then total_revenue / total_items_sold
            else 0
        end as revenue_per_item,
        
        case 
            when unique_customers > 0 then total_orders::float / unique_customers::float
            else 0
        end as orders_per_customer,
        
        -- Quality metrics
        orders_with_discrepancy,
        orders_with_future_date,
        orders_with_negative_amount,
        
        case 
            when total_orders > 0 then orders_with_discrepancy::float / total_orders::float
            else 0
        end as discrepancy_rate,
        
        -- Metadata
        current_timestamp as dbt_loaded_at,
        current_timestamp as dbt_updated_at
        
    from daily_metrics
)

select * from final
