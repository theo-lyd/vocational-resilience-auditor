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
    cast(hospitals_count as double) as hospitals_count,
    cast(total_beds as double) as total_beds,
    cast(beds_surgery as double) as beds_surgery,
    cast(beds_internal_medicine as double) as beds_internal_medicine,
    cast(beds_pediatrics as double) as beds_pediatrics,
    cast(beds_geriatrics as double) as beds_geriatrics,
    cast(beds_neurology as double) as beds_neurology,
    cast(beds_orthopedics as double) as beds_orthopedics,
    cast(beds_psychiatry as double) as beds_psychiatry
from read_parquet('{{ var("bronze_dir") }}/hospital_capacity.parquet')
where year is not null
  and (
    regexp_full_match(trim(ags), '^[0-9]{5}$')
    or regexp_full_match(trim(ags), '^[0-9]{8}$')
  )
