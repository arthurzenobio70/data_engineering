
{{
  config(
    materialized='view',
    docs={'node_color': 'lightblue'}
  )
}}

with source_data as (
    select * from {{ source('raw_data', 'customers') }}
),

renamed as (
    select
        -- Primary key
        id as customer_id,
        
        -- Customer attributes
        name as customer_name,
        email as customer_email,
        country as customer_country,
        
        -- Metadata
        {{ dbt_utils.generate_surrogate_key(['id']) }} as customer_key,
        current_timestamp as dbt_loaded_at,
        current_timestamp as dbt_updated_at
        
    from source_data
),

final as (
    select
        customer_id,
        customer_key,
        customer_name,
        lower(trim(customer_email)) as customer_email,
        upper(trim(customer_country)) as customer_country,
        
        -- Data quality flags
        case 
            when customer_email is null or customer_email = '' then true
            else false
        end as is_email_missing,
        
        case 
            when customer_name is null or customer_name = '' then true
            else false
        end as is_name_missing,
        
        dbt_loaded_at,
        dbt_updated_at
        
    from renamed
)

select * from final
