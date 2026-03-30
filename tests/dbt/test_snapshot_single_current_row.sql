select
    ags,
    district_name,
    school_type,
    year,
    count(*) as active_row_count
from {{ ref('snp_vocational_enrollment_scd2') }}
where dbt_valid_to is null
group by 1, 2, 3, 4
having count(*) > 1