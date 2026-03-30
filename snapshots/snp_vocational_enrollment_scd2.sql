{% snapshot snp_vocational_enrollment_scd2 %}

{{
    config(
        target_schema='main',
        unique_key="concat(ags, '|', district_name, '|', school_type, '|', cast(year as varchar))",
        strategy='check',
        check_cols=[
            'students_total',
            'students_female',
            'students_foreign',
            'ags_quality_flag'
        ],
        invalidate_hard_deletes=True
    )
}}

select
    ags,
    school_type,
    year,
    district_name,
    students_total,
    students_female,
    students_foreign,
    ags_quality_flag
from {{ ref('stg_vocational_enrollment') }}
where ags is not null
    and district_name is not null
  and school_type is not null

{% endsnapshot %}