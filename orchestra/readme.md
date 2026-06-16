# Orchestra (Dagster)

Orchestrates the CarbonMapping data pipeline:

1. Pull EIA hourly fuel-type data (`pull_and_sync_energy_data.py`)
2. Run dbt models (`dbt/`)
3. Validate idempotency (`audit.py`)

## Setup

```bash
cd orchestra
pip install -e .