-- models/Intermediate/int_generation_with_emissions.sql

with generation as (
    select * from {{ ref('stg_eia__energy_data_w_fuel_type') }}
),

emissions_factors as (
    select * from {{ ref('emissions_factors') }}
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
        ef.emissions_factor_gco2_per_kwh
    from generation as g
    left join emissions_factors as ef
        on g.fuel_type_name = ef.fuel_type_name
),

with_emissions as (
    select
        *,
        -- Hourly MW ≈ MWh for that hour; convert to kWh then apply g/kWh factor
        generation_mw * 1000.0 * emissions_factor_gco2_per_kwh as co2_grams
    from joined
)

select * from with_emissions