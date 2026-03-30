with metrics as (
    select
        avg(case when total_beds is not null then 1.0 else 0.0 end) as completeness_ratio
    from {{ ref('stg_hospital_capacity') }}
)
select *
from metrics
where completeness_ratio < 0.84