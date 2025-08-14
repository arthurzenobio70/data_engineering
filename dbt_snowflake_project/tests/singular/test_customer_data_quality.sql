-- Singular test for customer data quality issues
-- Identifies potential data quality problems in customer data

{{ config(tags=['data_quality']) }}

with customer_quality_checks as (
    select
        customer_id,
        customer_name,
        customer_email,
        customer_country,
        
        -- Quality flags
        case when customer_name is null or trim(customer_name) = '' then 1 else 0 end as missing_name,
        case when customer_email is null or trim(customer_email) = '' then 1 else 0 end as missing_email,
        case when customer_country is null or trim(customer_country) = '' then 1 else 0 end as missing_country,
        case when not regexp_like(customer_email, '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$') then 1 else 0 end as invalid_email,
        case when length(customer_name) > 100 then 1 else 0 end as name_too_long,
        
        -- Aggregate quality score
        (case when customer_name is null or trim(customer_name) = '' then 1 else 0 end +
         case when customer_email is null or trim(customer_email) = '' then 1 else 0 end +
         case when customer_country is null or trim(customer_country) = '' then 1 else 0 end +
         case when not regexp_like(customer_email, '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$') then 1 else 0 end +
         case when length(customer_name) > 100 then 1 else 0 end) as quality_issues_count
         
    from {{ ref('stg_customers') }}
)

select *
from customer_quality_checks
where quality_issues_count > 1  -- Flag customers with multiple quality issues
