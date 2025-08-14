-- Macro to generate standardized data quality flags
-- Usage: {{ data_quality_flags('column_name', 'data_type') }}

{% macro data_quality_flags(column_name, data_type='string') %}

    {% if data_type == 'string' %}
        case 
            when {{ column_name }} is null or trim({{ column_name }}) = '' then true
            else false
        end as {{ column_name }}_is_missing,
        
        case 
            when length({{ column_name }}) > 1000 then true
            else false
        end as {{ column_name }}_is_too_long,
        
        case 
            when {{ column_name }} like '%test%' or {{ column_name }} like '%dummy%' then true
            else false
        end as {{ column_name }}_is_test_data
        
    {% elif data_type == 'numeric' %}
        case 
            when {{ column_name }} is null then true
            else false
        end as {{ column_name }}_is_null,
        
        case 
            when {{ column_name }} < 0 then true
            else false
        end as {{ column_name }}_is_negative,
        
        case 
            when {{ column_name }} = 0 then true
            else false
        end as {{ column_name }}_is_zero,
        
        case 
            when abs({{ column_name }}) > 1000000 then true
            else false
        end as {{ column_name }}_is_outlier
        
    {% elif data_type == 'date' %}
        case 
            when {{ column_name }} is null then true
            else false
        end as {{ column_name }}_is_null,
        
        case 
            when {{ column_name }} > current_date then true
            else false
        end as {{ column_name }}_is_future,
        
        case 
            when {{ column_name }} < '1900-01-01' then true
            else false
        end as {{ column_name }}_is_too_old,
        
        case 
            when extract(year from {{ column_name }}) < 2000 then true
            else false
        end as {{ column_name }}_is_pre_2000
        
    {% endif %}

{% endmacro %}
