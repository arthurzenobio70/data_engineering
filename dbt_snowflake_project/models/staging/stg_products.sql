
{{
  config(
    materialized='view',
    docs={'node_color': 'lightblue'}
  )
}}

with source_data as (
    select * from {{ source('raw_data', 'products') }}
),

renamed as (
    select
        -- Primary key
        id as product_id,
        
        -- Product attributes
        name as product_name,
        category as product_category,
        price as product_price,
        
        -- Metadata
        {{ dbt_utils.generate_surrogate_key(['id']) }} as product_key,
        current_timestamp as dbt_loaded_at,
        current_timestamp as dbt_updated_at
        
    from source_data
),

final as (
    select
        product_id,
        product_key,
        trim(product_name) as product_name,
        upper(trim(product_category)) as product_category,
        product_price,
        
        -- Product classifications
        case 
            when product_price < 25 then 'budget'
            when product_price < 100 then 'standard'
            when product_price < 500 then 'premium'
            else 'luxury'
        end as price_segment,
        
        case 
            when upper(product_category) in ('ELECTRONICS', 'GADGETS') then 'tech'
            when upper(product_category) in ('CLOTHING', 'FASHION', 'ACCESSORIES') then 'apparel'
            when upper(product_category) in ('HOME', 'FURNITURE', 'KITCHEN') then 'home'
            when upper(product_category) in ('BOOKS', 'MEDIA', 'ENTERTAINMENT') then 'media'
            else 'other'
        end as category_group,
        
        -- Business flags
        case 
            when product_price > 1000 then true
            else false
        end as is_high_value,
        
        case 
            when upper(product_category) = 'ELECTRONICS' then true
            else false
        end as is_electronics,
        
        -- Data quality flags
        case 
            when product_name is null or trim(product_name) = '' then true
            else false
        end as is_name_missing,
        
        case 
            when product_category is null or trim(product_category) = '' then true
            else false
        end as is_category_missing,
        
        case 
            when product_price <= 0 then true
            else false
        end as has_invalid_price,
        
        dbt_loaded_at,
        dbt_updated_at
        
    from renamed
)

select * from final
