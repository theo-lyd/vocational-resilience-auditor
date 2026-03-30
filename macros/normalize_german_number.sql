{% macro normalize_german_number(column_name) -%}
  cast(replace(replace({{ column_name }}, '.', ''), ',', '.') as double)
{%- endmacro %}
