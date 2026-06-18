# CarbonMapping Orchestra

**Hourly grid carbon intensity, end to end.**  

This pipeline pulls real-time electricity generation data for the New England grid. Calculates how much carbon the grid is emitting each hour. Surfaces the cleanest times to use power. Ingesting from a live API, transforming through dbt, orchestrated with Dagster

```mermaid
flowchart LR
    A[EIA-930 API] --> B[Ingestion]
    B --> C[(Postgres / RDS)]
    C --> D[dbt transforms]
    D --> E[Dagster orchestration]
    E --> F[Power BI dashboard]
```

> **Why it matters:** Grid carbon intensity changes hour by hour. Utilities, EV charging apps. Sustainability teams need a reliable, repeatable pipeline. This project turns public EIA data into queryable carbon metrics.

---

### Pipeline (Dagster)
![Dagster asset lineage: EIA ingestion → dbt staging → intermediate emissions join → marts](docs/screenshots/dagster-lineage.jpg)


*Asset graph: `energy_data_w_fuel_type` → staging → `int_generation_with_emissions` → `hourly_intensity`, `mart_fuel_mix`, `daily_rollup`.*


### Output (Power BI)
![Power BI dashboard: daily and hourly carbon intensity, emissions share by fuel type](docs/screenshots/powerbi-dashboard.jpg)
*Dashboard fed from `marts.hourly_intensity`, `marts.mart_fuel_mix`, and `daily_rollup` — daily intensity trends, hourly patterns, fuel-mix shifts (e.g. gas vs hydro).*