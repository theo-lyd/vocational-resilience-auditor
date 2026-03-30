select distinct
    dataset_name,
    gender_code,
    gender_label,
    degree_code,
    degree_label
from {{ ref('stg_vocational_graduates') }}
