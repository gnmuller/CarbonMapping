import os
from datetime import datetime, timedelta, timezone

import psycopg2
from dagster import AssetExecutionContext, MetadataValue, asset,AssetKey

from carbonmapping_dagster.ingestion.eia_client import (
    fetch_eia_fuel_type_data,
    upsert_raw_generation,
)

WINDOW_DAYS = 60

@asset(
    key=AssetKey(["eia", "energy_data_w_fuel_type"]),
    description="Hourly EIA RTO fuel-type data landed in public.energy_data_w_fuel_type",
    group_name="ingestion",
)
def eia_fuel_type_raw_w_fuel_type(context: AssetExecutionContext) -> int:
    now = datetime.now(timezone.utc)
    end = now.replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(days=WINDOW_DAYS)

    context.log.info("Fetching EIA data from %s to %s", start, end)

    rows = fetch_eia_fuel_type_data(start, end, os.environ["EIA_API_KEY"])

    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        database=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        port=os.environ.get("POSTGRES_PORT", "5432"),
    )
    try:
        row_count = upsert_raw_generation(rows, conn)
    finally:
        conn.close()

    context.add_output_metadata({
        "row_count": MetadataValue.int(row_count),
        "window_start": MetadataValue.text(start.isoformat()),
        "window_end": MetadataValue.text(end.isoformat()),
    })
    return row_count
