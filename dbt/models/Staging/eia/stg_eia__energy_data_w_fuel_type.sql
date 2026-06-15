-- models/staging/eia/stg_eia__energy_data_w_fuel_type.sql

with source as (
    select * from {{ source('eia', 'energy_data_w_fuel_type') }}
),

renamed as (
    select
        id as energy_data_id,
        period::timestamptz as period_utc,
        respondent,
        respondent_name,
        fueltype as fuel_type,
        type_name as fuel_type_name,
        value::numeric as generation_mw,
        value_units as generation_units,
        created_at::timestamptz as loaded_at,
        extract(hour from period)::int as period_hour
    from source
),

filtered as (
    select *
    from renamed
    where period_utc is not null
      and respondent is not null
      and fuel_type is not null
      and generation_mw is not null
)

select * from filtered