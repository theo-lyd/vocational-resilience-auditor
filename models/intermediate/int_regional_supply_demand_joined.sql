with graduates_latest as (
    select
        ags,
        year as graduate_year,
        sum(graduates) as graduates_total,
        row_number() over (partition by ags order by year desc) as rn
    from {{ ref('stg_vocational_graduates') }}
    where dataset_name = 'DS_003'
      and gender_code = '%TOTAL%'
    group by 1, 2
),
graduates as (
    select *
    from graduates_latest
    where rn = 1
),
hospital_latest as (
    select *
    from (
        select
            ags,
            district_name,
            year as hospital_year,
            total_beds,
            beds_surgery,
            beds_internal_medicine,
            beds_geriatrics,
            beds_pediatrics,
            beds_neurology,
            beds_orthopedics,
            beds_psychiatry,
            row_number() over (partition by ags order by year desc) as rn
        from {{ ref('stg_hospital_capacity') }}
    ) ranked
    where rn = 1
),
enrollment_latest as (
    select *
    from (
        select
            ags,
            year as enrollment_year,
            students_total,
            students_female,
            students_foreign,
            row_number() over (partition by ags order by year desc) as rn
        from {{ ref('stg_vocational_enrollment') }}
        where school_type = 'Insgesamt'
    ) ranked
    where rn = 1
)
select
    coalesce(g.ags, h.ags, e.ags) as ags,
    h.district_name,
    g.graduate_year,
    e.enrollment_year,
    g.graduates_total,
    e.students_total,
    e.students_female,
    e.students_foreign,
    h.hospital_year,
    h.total_beds,
    h.beds_surgery,
    h.beds_internal_medicine,
    h.beds_geriatrics,
    h.beds_pediatrics,
    h.beds_neurology,
    h.beds_orthopedics,
    h.beds_psychiatry,
    coalesce(g.graduates_total, 0) - coalesce(h.total_beds, 0) as supply_demand_gap,
    case
        when h.total_beds is null or h.total_beds = 0 then null
        else g.graduates_total / h.total_beds
    end as supply_demand_ratio,
    case
        when h.total_beds is null or h.total_beds = 0 then null
        else h.beds_psychiatry / h.total_beds
    end as psychiatry_capacity_share,
    case
        when h.total_beds is null or h.total_beds = 0 then null
        else h.beds_geriatrics / h.total_beds
    end as geriatrics_capacity_share
from graduates g
full outer join hospital_latest h on g.ags = h.ags
full outer join enrollment_latest e on coalesce(g.ags, h.ags) = e.ags
