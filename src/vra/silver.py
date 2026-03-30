from __future__ import annotations

import duckdb


def build_silver_layer(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        create or replace table silver_vocational_enrollment as
        select
            year,
            case
                when regexp_full_match(trim(ags), '^[0-9]{5}$') then trim(ags)
                when regexp_full_match(trim(ags), '^[0-9]{8}$') then substring(trim(ags), 1, 5)
                else null
            end as ags,
            length(trim(ags)) as ags_source_length,
            case
                when regexp_full_match(trim(ags), '^[0-9]{5}$') then 'district_direct'
                when regexp_full_match(trim(ags), '^[0-9]{8}$') then 'municipality_rolled_up'
                else 'invalid_ags'
            end as ags_quality_flag,
            trim(district_name) as district_name,
            trim(school_type) as school_type,
            schools_count::double as schools_count,
            students_total::double as students_total,
            students_female::double as students_female,
            students_foreign::double as students_foreign
        from bronze_vocational_enrollment
        where year is not null
          and ags is not null
          and school_type is not null
        """
    )

    con.execute(
        """
        create or replace table silver_vocational_enrollment_totals as
        select
            year,
            ags,
                        ags_source_length,
                        ags_quality_flag,
            district_name,
            students_total,
            students_female,
            students_foreign
        from silver_vocational_enrollment
        where lower(school_type) = 'insgesamt'
                    and ags is not null
        """
    )

    con.execute(
        """
        create or replace table silver_hospital_capacity as
        select
            year,
            case
                when regexp_full_match(trim(ags), '^[0-9]{5}$') then trim(ags)
                when regexp_full_match(trim(ags), '^[0-9]{8}$') then substring(trim(ags), 1, 5)
                else null
            end as ags,
            length(trim(ags)) as ags_source_length,
            case
                when regexp_full_match(trim(ags), '^[0-9]{5}$') then 'district_direct'
                when regexp_full_match(trim(ags), '^[0-9]{8}$') then 'municipality_rolled_up'
                else 'invalid_ags'
            end as ags_quality_flag,
            trim(district_name) as district_name,
            hospitals_count::double as hospitals_count,
            total_beds::double as total_beds,
            beds_internal_medicine::double as beds_internal_medicine,
            beds_pediatrics::double as beds_pediatrics,
            beds_geriatrics::double as beds_geriatrics,
            beds_psychiatry::double as beds_psychiatry
        from bronze_hospital_capacity
        where year is not null
          and ags is not null
          and total_beds is not null
        """
    )

    con.execute("delete from silver_hospital_capacity where ags is null")

    con.execute(
        """
        create or replace table silver_vocational_graduates as
        select
            year,
            case
                when regexp_full_match(trim(ags), '^[0-9]{5}$') then trim(ags)
                when regexp_full_match(trim(ags), '^[0-9]{8}$') then substring(trim(ags), 1, 5)
                else null
            end as ags,
            length(trim(ags)) as ags_source_length,
            case
                when regexp_full_match(trim(ags), '^[0-9]{5}$') then 'district_direct'
                when regexp_full_match(trim(ags), '^[0-9]{8}$') then 'municipality_rolled_up'
                else 'invalid_ags'
            end as ags_quality_flag,
            dataset_name,
            coalesce(gender_code, '%TOTAL%') as gender_code,
            case
                when coalesce(gender_code, '%TOTAL%') = '%TOTAL%' then 'Total'
                when gender_code = 'GESM' then 'Male'
                when gender_code = 'GESW' then 'Female'
                when gender_code = 'GESD' then 'Diverse or unspecified'
                else concat('Unknown gender code: ', coalesce(gender_code, 'NULL'))
            end as gender_label,
            degree_code,
            case
                when degree_code is null then 'Total graduates'
                when degree_code = 'BILABB12' then 'Lower secondary qualification'
                when degree_code = 'BILABB13' then 'Intermediate qualification'
                when degree_code = 'BILABB14' then 'University of applied sciences entrance qualification'
                when degree_code = 'BILABB15' then 'General higher education entrance qualification'
                else concat('Unknown degree code: ', degree_code)
            end as degree_label,
            value::double as graduates
        from bronze_vocational_graduates
        where year is not null
          and ags is not null
          and value is not null
        """
    )

    con.execute("delete from silver_vocational_graduates where ags is null")

    con.execute(
        """
        create or replace table silver_vocational_graduates_codebook as
        select distinct
            dataset_name,
            gender_code,
            gender_label,
            degree_code,
            degree_label
        from silver_vocational_graduates
        """
    )

    con.execute(
        """
        create or replace table silver_vocational_graduates_total as
        select
            year,
            ags,
            sum(graduates) as graduates_total
        from silver_vocational_graduates
        where dataset_name = 'DS_003'
          and gender_code = '%TOTAL%'
        group by 1, 2
        """
    )
