{#
    generate_schema_name — the custom schema, verbatim (spec: naming_and_layout).

    dbt's default renders <target.schema>_<custom_schema_name> (dev_cleansed_musicbrainz), which
    would put the target in front of every schema. Here the folder's +schema IS the schema
    (cleansed_musicbrainz, staging_musicbrainz, modeled_music, report_music), and the target
    chooses the data root instead (data/<target>/ through dbt_project.yml's location_root). A
    model with no +schema — none should exist — falls back to target.schema, which profiles.yml
    names after the target so the stray is easy to spot.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}

    {%- if custom_schema_name is none -%}

        {{ target.schema }}

    {%- else -%}

        {{ custom_schema_name | trim }}

    {%- endif -%}

{%- endmacro %}
