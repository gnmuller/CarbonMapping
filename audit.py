"""Verify the energy data sync pipeline is idempotent."""

import os

import psycopg2
from dotenv import load_dotenv

from pull_and_sync_energy_data import main as run_pipeline

load_dotenv()

SNAPSHOT_QUERY = """
SELECT period, respondent, respondent_name, fueltype, type_name, value, value_units
FROM energy_data_w_fuel_type
ORDER BY period, respondent, fueltype
"""


def connect():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        database=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        port=os.environ.get("POSTGRES_PORT", "5432"),
    )


def snapshot(conn):
    with conn.cursor() as cur:
        cur.execute(SNAPSHOT_QUERY)
        return cur.fetchall()


def main():
    conn = connect()
    try:
        before = snapshot(conn)
    finally:
        conn.close()

    run_pipeline()

    conn = connect()
    try:
        after = snapshot(conn)
    finally:
        conn.close()

    if before != after:
        raise AssertionError(
            f"Data differs after re-run ({len(before)} rows before, {len(after)} after)"
        )

    print(f"Audit passed: {len(before)} rows unchanged after pipeline re-run.")


if __name__ == "__main__":
    main()
