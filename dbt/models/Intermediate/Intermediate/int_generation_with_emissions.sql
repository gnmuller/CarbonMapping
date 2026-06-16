with generation as (
    select * from {{ ref('stg_eia__energy_data_w_fuel_type') }}
),

emissions_factors as (
    select * from {{ ref('emissions_factors') }}
),

default_factor as (
    select emissions_factor_gco2_per_kwh as default_emissions_factor_gco2_per_kwh
    from emissions_factors
    where fuel_type_name = 'Other'
),

joined as (
    select
        g.energy_data_id,
        g.period_utc,
        g.period_hour,
        g.respondent,
        g.respondent_name,
        g.fuel_type,
        g.fuel_type_name,
        g.generation_mw,
        g.generation_units,
        g.loaded_at,
        ef.emissions_factor_gco2_per_kwh as raw_emissions_factor_gco2_per_kwh
    from generation as g
    left join emissions_factors as ef
        on g.fuel_type_name = ef.fuel_type_name
),

with_emissions as (
    select
        j.*,
        coalesce(
            j.raw_emissions_factor_gco2_per_kwh,
            d.default_emissions_factor_gco2_per_kwh
        ) as emissions_factor_gco2_per_kwh,
        (j.raw_emissions_factor_gco2_per_kwh is null) as is_emissions_factor_imputed,
        j.generation_mw * 1000.0 * coalesce(
            j.raw_emissions_factor_gco2_per_kwh,
            d.default_emissions_factor_gco2_per_kwh
        ) as co2_grams
    from joined as j
    cross join default_factor as d
)

select
    energy_data_id,
    period_utc,
    period_hour,
    respondent,
    respondent_name,
    fuel_type,
    fuel_type_name,
    generation_mw,
    generation_units,
    loaded_at,
    emissions_factor_gco2_per_kwh,
    is_emissions_factor_imputed,
    co2_grams
from with_emissions