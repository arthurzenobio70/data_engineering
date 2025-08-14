{{
  config(
    materialized='view',
    docs={'node_color': 'lightblue'}
  )
}}

with source_data as (
    select * from {{ source('raw_data', 'orders') }}
),

renamed as (
    select
        -- Primary key
        id as order_id,
        
        -- Foreign keys
        customer_id,
        
        -- Order attributes
        order_date,
        total_amount,
        status as order_status,
        
        -- Metadata
        {{ dbt_utils.generate_surrogate_key(['id']) }} as order_key,
        current_timestamp as dbt_loaded_at,
        current_timestamp as dbt_updated_at
        
    from source_data
),

final as (
    select
        order_id,
        order_key,
        customer_id,
        order_date,
        total_amount,
        upper(trim(order_status)) as order_status,
        
        -- Date extractions
        extract(year from order_date) as order_year,
        extract(month from order_date) as order_month,
        extract(day from order_date) as order_day,
        extract(dayofweek from order_date) as order_day_of_week,
        
        -- Business logic flags
        case 
            when order_status in ('COMPLETED', 'SHIPPED') then true
            else false
        end as is_order_completed,
        
        case 
            when order_status = 'CANCELLED' then true
            else false
        end as is_order_cancelled,
        
        case 
            when order_date >= current_date - 30 then true
            else false
        end as is_recent_order,
        
        -- Data quality flags
        case 
            when total_amount < 0 then true
            else false
        end as has_negative_amount,
        
        case 
            when order_date > current_date then true
            else false
        end as has_future_date,
        
        dbt_loaded_at,
        dbt_updated_at
        
    from renamed
)

select * from final
