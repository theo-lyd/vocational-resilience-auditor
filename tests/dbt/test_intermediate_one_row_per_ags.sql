select
    ags,
    count(*) as district_rows
from {{ ref('int_regional_supply_demand_joined') }}
group by 1
having count(*) > 1