-- models/Marts/hourly_intensity.sql

select
    period_utc,
    respondent,
    respondent_name,
    period_hour,
    sum(co2_grams) as total_co2_grams,
    sum(generation_mw) as total_generation_mw,
    sum(co2_grams) / nullif(sum(generation_mw) * 1000.0, 0) as carbon_intensity_g_per_kwh
from {{ ref('int_generation_with_emissions') }}
group by 1, 2, 3, 4