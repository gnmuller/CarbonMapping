# Orchestra (Dagster)

Orchestrates the CarbonMapping data pipeline via Dagster assets in `carbonmapping_dagster/`:

1. **Ingestion** — `eia_fuel_type_raw_w_fuel_type` lands hourly EIA RTO fuel-type data in `public.energy_data_w_fuel_type` (60-day rolling window).
2. **Transform** — `carbonmapping_dbt_assets` runs `dbt build` against the project in `../dbt/`.
3. **Marts** — `hourly_intensity`, `mart_fuel_mix`, and `daily_rollup` for downstream reporting.

Asset lineage: `eia/energy_data_w_fuel_type` → `stg_eia__energy_data_w_fuel_type` → `int_generation_with_emissions` → marts.

## Setup

From the repo root, create a `.env` with:

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

## Run

Load env vars, then start the Dagster UI (module entry point is set in `pyproject.toml`):

```bash
cd orchestra
dagster dev
```

Open the UI (default `http://127.0.0.1:3000`), materialize assets from the graph, or run the full pipeline via **Materialize all**.

Legacy scripts at the repo root (`pull_and_sync_energy_data.py`, `audit.py`) predate this Dagster orchestration and are not used by `dagster dev`.
