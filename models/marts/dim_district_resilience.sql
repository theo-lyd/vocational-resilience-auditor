select
    ags,
    district_name,
    graduate_year,
    graduates_total as graduates_latest,
    students_total as enrollment_latest,
    hospital_year,
    total_beds,
    supply_demand_gap,
    supply_demand_ratio as resilience_score,
    case
        when supply_demand_ratio is null then 'Missing demand baseline'
        when supply_demand_ratio < 1.0 then 'Systemic Risk'
        when supply_demand_ratio < 2.0 then 'Watch'
        else 'Resilient'
    end as risk_band
from {{ ref('int_regional_supply_demand_joined') }}
