-- Custom generic test to check for positive values
-- Usage: {{ config(tags=['data_quality']) }}

{% test positive_values(model, column_name) %}

  select *
  from {{ model }}
  where {{ column_name }} <= 0

{% endtest %}
