-- Macro to generate standardized business metrics
-- Usage: {{ get_business_metrics('revenue_column', 'count_column') }}

{% macro get_business_metrics(revenue_col, count_col) %}
    
    -- Basic metrics
    sum({{ revenue_col }}) as total_revenue,
    avg({{ revenue_col }}) as avg_revenue,
    median({{ revenue_col }}) as median_revenue,
    min({{ revenue_col }}) as min_revenue,
    max({{ revenue_col }}) as max_revenue,
    
    sum({{ count_col }}) as total_count,
    count(distinct {{ count_col }}) as unique_count,
    
    -- Advanced metrics
    stddev({{ revenue_col }}) as revenue_stddev,
    variance({{ revenue_col }}) as revenue_variance,
    
    -- Percentiles
    percentile_cont(0.25) within group (order by {{ revenue_col }}) as revenue_p25,
    percentile_cont(0.75) within group (order by {{ revenue_col }}) as revenue_p75,
    percentile_cont(0.90) within group (order by {{ revenue_col }}) as revenue_p90,
    percentile_cont(0.95) within group (order by {{ revenue_col }}) as revenue_p95
    
{% endmacro %}
