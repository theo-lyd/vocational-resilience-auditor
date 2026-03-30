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
    cast(value as double) as graduates
from read_parquet('{{ var("bronze_dir") }}/vocational_graduates.parquet')
where year is not null
  and ags is not null
  and value is not null
  and (
    regexp_full_match(trim(ags), '^[0-9]{5}$')
    or regexp_full_match(trim(ags), '^[0-9]{8}$')
  )
