-- Custom generic test to validate email format
-- Usage: {{ config(tags=['data_quality']) }}

{% test valid_email(model, column_name) %}

  select *
  from {{ model }}
  where {{ column_name }} is not null
    and not regexp_like({{ column_name }}, '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$')

{% endtest %}
