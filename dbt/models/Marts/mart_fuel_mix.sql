-- models/Marts/mart_fuel_mix.sql

with hourly_by_fuel as (
    select
        period_utc,
        period_hour,
        respondent,
        respondent_name,
        fuel_type,
        fuel_type_name,
        sum(generation_mw) as generation_mw,
        sum(co2_grams) as co2_grams
    from {{ ref('int_generation_with_emissions') }}
    group by 1, 2, 3, 4, 5, 6
),

with_shares as (
    select
        *,
        sum(generation_mw) over (
            partition by period_utc, respondent
        ) as total_generation_mw,
        sum(co2_grams) over (
            partition by period_utc, respondent
        ) as total_co2_grams
    from hourly_by_fuel
)

select
    period_utc,
    period_hour,
    respondent,
    respondent_name,
    fuel_type,
    fuel_type_name,
    generation_mw,
    co2_grams,
    total_generation_mw,
    total_co2_grams,
    generation_mw / nullif(total_generation_mw, 0) as generation_share,
    co2_grams / nullif(total_co2_grams, 0) as emissions_share
from with_shares