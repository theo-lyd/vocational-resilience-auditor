with versions as (
    select
        dbt_scd_id,
        ags,
        district_name,
        school_type,
        year,
        dbt_valid_from as valid_from,
        coalesce(dbt_valid_to, cast('9999-12-31' as timestamp)) as valid_to
    from {{ ref('snp_vocational_enrollment_scd2') }}
),
overlap_rows as (
    select
        a.ags,
        a.district_name,
        a.school_type,
        a.year,
        a.dbt_scd_id as left_version,
        b.dbt_scd_id as right_version,
        a.valid_from as left_from,
        a.valid_to as left_to,
        b.valid_from as right_from,
        b.valid_to as right_to
    from versions a
    join versions b
        on a.ags = b.ags
        and a.district_name = b.district_name
       and a.school_type = b.school_type
        and a.year = b.year
       and a.dbt_scd_id < b.dbt_scd_id
       and a.valid_from < b.valid_to
       and b.valid_from < a.valid_to
)
select *
    from overlap_rows