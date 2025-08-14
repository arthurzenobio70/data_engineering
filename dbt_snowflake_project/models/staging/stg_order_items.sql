{{
  config(
    materialized='view',
    docs={'node_color': 'lightblue'}
  )
}}

with source_data as (
    select * from {{ source('raw_data', 'order_items') }}
),

renamed as (
    select
        -- Primary key
        id as item_id,
        
        -- Foreign keys
        order_id,
        product_id,
        
        -- Item attributes
        quantity,
        unit_price,
        
        -- Metadata
        {{ dbt_utils.generate_surrogate_key(['id']) }} as item_key,
        current_timestamp as dbt_loaded_at,
        current_timestamp as dbt_updated_at
        
    from source_data
),

final as (
    select
        item_id,
        item_key,
        order_id,
        product_id,
        quantity,
        unit_price,
        
        -- Calculated fields
        (quantity * unit_price) as total_price,
        case 
            when quantity > 1 then (quantity * unit_price) / quantity
            else unit_price
        end as effective_unit_price,
        
        -- Business logic flags
        case 
            when quantity > 10 then true
            else false
        end as is_bulk_order,
        
        case 
            when unit_price < 10 then 'low'
            when unit_price < 100 then 'medium'
            else 'high'
        end as price_tier,
        
        -- Data quality flags
        case 
            when quantity <= 0 then true
            else false
        end as has_invalid_quantity,
        
        case 
            when unit_price < 0 then true
            else false
        end as has_negative_price,
        
        case 
            when (quantity * unit_price) != (quantity * unit_price) then true
            else false
        end as has_calculation_error,
        
        dbt_loaded_at,
        dbt_updated_at
        
    from renamed
)

select * from final
