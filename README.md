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

## Design choices

Deliberate tradeoffs behind the stack. Not defaults picked for familiarity.

### Dagster over Airflow

Airflow is task-centric: Wiring operators and trusting the DAG. Dagster is more asset-centric: Declaring things that should exist (raw generation, transformed marts) and it figures out the flow. Closer allignment to the pipeline — data moving through stages — and the local setup is lighter, which mattered more for a solo project. 

### dbt over transformation-in-Python

Cleaning and rollups could live in pandas. See (pull_and_sync_energy_data.py ) The transformation logic is buried in Python. Invisible and untested. dbt pulls that logic into one versioned place ([`dbt/`](dbt/)), makes model lineage explicit in the Dagster graph, and runs assertions (no nulls, valid fuel types in [`eia_models.yml`](dbt/models/Staging/eia/eia_models.yml)) that fail loudly before bad data reaches the chart.

### Idempotent ingestion

A scheduled job that double-writes every run corrupts its own table. Ingestion is built to be safe to re-run: same window, same result, no duplicates — `ON CONFLICT` upserts on `(period, respondent, fueltype)` in [`eia_client.py`](orchestra/carbonmapping_dagster/ingestion/eia_client.py). That's the precondition for scheduling anything at all; without it, orchestration just multiplies the bug faster.

### Real EIA data, not synthetic

Synthetic data is easy. Real grid data is messy. Gaps, late-arriving hours, fuel types that drop in and out. Handling that mess is the work. Pulling from the live EIA-930 API also gives the pipeline a real reason to run on a schedule, which is the whole point of orchestrating it.

---


---

## How it runs

The pipeline lives in [`orchestra/`](orchestra/) and is driven by Dagster assets — no manual scripts required.

### Prerequisites

- Postgres (local or RDS)
- EIA API key ([register at eia.gov](https://www.eia.gov/opendata/register.php))

Create a `.env` at the repo root:

```
EIA_API_KEY=
POSTGRES_HOST=localhost
POSTGRES_DB=CarbonMapping
POSTGRES_USER=postgres
POSTGRES_PASSWORD=
POSTGRES_PORT=5435
```

Install the Dagster package:

```bash
cd orchestra
pip install -e .
```

### Run

```bash
cd orchestra
dagster dev
```

Open `http://127.0.0.1:3000`, then **Materialize all** (or select assets in the graph).

Each run:

1. **Ingestion** — `eia_fuel_type_raw_w_fuel_type` pulls the last 60 days of hourly fuel-type generation from the EIA-930 API and upserts into `public.energy_data_w_fuel_type`.
2. **Transform** — `carbonmapping_dbt_assets` runs `dbt build` against [`dbt/`](dbt/): staging → `int_generation_with_emissions` (generation × IPCC emission factors) → marts (`hourly_intensity`, `mart_fuel_mix`, `daily_rollup`).
3. **Consume** — marts tables in Postgres feed downstream tools (e.g. Power BI).

Legacy root scripts (`pull_and_sync_energy_data.py`, `audit.py`, `carbon_intensity_calc.py`) predate Dagster orchestration and are not invoked by `dagster dev`.

---

### Pipeline (Dagster)
![Dagster asset lineage: EIA ingestion → dbt staging → intermediate emissions join → marts](docs/screenshots/dagster-lineage.jpg)


*Asset graph: `energy_data_w_fuel_type` → staging → `int_generation_with_emissions` → `hourly_intensity`, `mart_fuel_mix`, `daily_rollup`.*


### Output (Power BI)
![Power BI dashboard: daily and hourly carbon intensity, emissions share by fuel type](docs/screenshots/powerbi-dashboard.jpg)
*Dashboard fed from `marts.hourly_intensity`, `marts.mart_fuel_mix`, and `daily_rollup` — daily intensity trends, hourly patterns, fuel-mix shifts (e.g. gas vs hydro).*


## What's next

The pipeline runs end-to-end locally. These are the highest-impact next steps to make it production-ready and aligned with the New England use case.

### Pipeline correctness
- **Fix `daily_rollup`** — Today it mirrors `[hourly_intensity](dbt/models/Marts/hourly_intensity.sql)`; aggregate to day (`date_trunc('day', period_utc)`) and add marts schema tests.
- **Scope to ISO-NE** — Ingestion pulls all EIA RTO respondents; filter to `ISNE` (or a configurable respondent list) in staging or a dedicated mart so metrics match the README narrative.
- **Tighten Dagster ↔ dbt lineage** — Link the ingestion asset (`eia/energy_data_w_fuel_type`) to the dbt source so the asset graph shows a clean dependency edge.

### Automation & reliability
- **Add a Dagster schedule** — Hourly or daily materialization of the full asset graph; idempotent upserts in `[eia_client.py](orchestra/carbonmapping_dagster/ingestion/eia_client.py)` are the precondition.
- **Source freshness & bounds checks** — dbt tests on `loaded_at`, imputed emission factors, and sane carbon-intensity ranges so bad API data fails before Power BI.
- **CI on PRs** — GitHub Action: `dbt parse`, `dbt test`, and optionally a small pytest for upsert/idempotency logic.

### Production path
- **Deploy orchestration** — Dagster Cloud or a self-hosted agent with managed Postgres (RDS); move `.env` secrets to a secrets manager.
- **Retire legacy scripts** — `[pull_and_sync_energy_data.py](pull_and_sync_energy_data.py)`, `[audit.py](audit.py)`, and `[carbon_intensity_calc.py](carbon_intensity_calc.py)` predate Dagster; consolidate or remove once the Dagster path is scheduled and tested.

### Downstream consumption
- **Expose marts via API** — REST or GraphQL over `marts.hourly_intensity` for EV-charging or sustainability tooling (called out in the README vision).
- **Extend regions or factors** — Additional ISOs, updated IPCC factors issue factors, or marginal vs average intensity if use cases require it.