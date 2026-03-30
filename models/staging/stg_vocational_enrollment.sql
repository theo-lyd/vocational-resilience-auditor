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
    cast(students_total as double) as students_total,
    cast(students_female as double) as students_female,
    cast(students_foreign as double) as students_foreign
from read_parquet('{{ var("bronze_dir") }}/vocational_enrollment.parquet')
where year is not null
  and (
      regexp_full_match(trim(ags), '^[0-9]{5}$')
      or regexp_full_match(trim(ags), '^[0-9]{8}$')
  )
