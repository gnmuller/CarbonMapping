import json
import os
from pathlib import Path

import psycopg2
import requests
from dotenv import load_dotenv

from psycopg2.extras import execute_values


from datetime import datetime, timedelta, timezone

load_dotenv()


def fetch_eia_fuel_type_data(start, end, api_key) -> list[dict]:
    params = {
        "api_key": api_key,
        "frequency": "hourly",
        "data[0]": "value",
        "start": start.strftime("%Y-%m-%dT%H"),   # e.g. 2026-04-13T00
        "end": end.strftime("%Y-%m-%dT%H"),         # e.g. 2026-06-12T00
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "offset": 0,
        "length": 5000,
    }


    BASE_URL = "https://api.eia.gov/v2/electricity/rto/fuel-type-data/data/"

    PAGE_SIZE = 5000
    all_rows = []
    offset = 0
    payload: dict = {}
    while True:
        response = requests.get(
            BASE_URL,
            params={
                **params,
                "offset": offset,
                "length": PAGE_SIZE,
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        batch = payload["response"]["data"]
        if not batch:
            break
        all_rows.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE





    payload["response"]["data"] = all_rows
    payload["response"]["total"] = len(all_rows)

    ingestion_dir = Path("ingestion")
    ingestion_dir.mkdir(exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = ingestion_dir / f"daily-region-sub-ba-data_{timestamp}.json"

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Saved to {output_path}")

    return all_rows



def upsert_raw_generation(all_rows: list[dict], conn) -> int:

    try:
        connection = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "localhost"),
            database=os.environ["POSTGRES_DB"],
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
            port=os.environ.get("POSTGRES_PORT", "5432"),
        )

        # 2. Create a cursor object to execute SQL commands
        cursor = connection.cursor()

        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        print(f"Successfully connected! PostgreSQL version: {db_version[0]}")

        create_table_query = """
        CREATE TABLE IF NOT EXISTS energy_data_w_fuel_type (
        id SERIAL PRIMARY KEY,
        period TIMESTAMP NOT NULL,
        respondent VARCHAR(50) NOT NULL,
        respondent_name VARCHAR(255) NOT NULL,
        fueltype VARCHAR(10) NOT NULL,
        type_name VARCHAR(255) NOT NULL,
        value NUMERIC(15, 2) NOT NULL,
        value_units VARCHAR(50) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(period, respondent, fueltype)
        );

        CREATE INDEX IF NOT EXISTS idx_fuel_type_period ON energy_data_w_fuel_type(period);
        CREATE INDEX IF NOT EXISTS idx_fuel_type_respondent ON energy_data_w_fuel_type(respondent);
        CREATE INDEX IF NOT EXISTS idx_fuel_type_fueltype ON energy_data_w_fuel_type(fueltype);
        """

        # 4. Execute the SQL command
        cursor.execute(create_table_query)

        upsert_query  = """
        INSERT INTO energy_data_w_fuel_type (
            period, respondent, respondent_name, fueltype, type_name, value, value_units
        ) VALUES %s
        ON CONFLICT (period, respondent, fueltype)
        DO UPDATE SET
            respondent_name = EXCLUDED.respondent_name,
            type_name = EXCLUDED.type_name,
            value = EXCLUDED.value,
            value_units = EXCLUDED.value_units;
            """

        rows = []
        for row in all_rows:
            period = datetime.fromisoformat(row["period"]).replace(tzinfo=timezone.utc)
            rows.append((
                period,
                row["respondent"],
                row["respondent-name"],
                row["fueltype"],
                row["type-name"],
                row["value"],
                row["value-units"],
            ))


        execute_values(cursor, upsert_query, rows, page_size=1000)

        # 5. Commit the transaction to save changes
        connection.commit()
        print("Table 'energy_data_w_fuel_type' synced successfully!")

        return len(all_rows)


    except Exception as error:
        print(f"Error while connecting to PostgreSQL: {error}")

    finally:
        # 6. Always close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            print("PostgreSQL connection closed.")




def main():




    
    WINDOW_DAYS = 60
    now = datetime.now(timezone.utc)
    end = now.replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(days=WINDOW_DAYS)

    print(f"Fetching data from {start} to {end}")








    api_key = os.environ["EIA_API_KEY"]


    params = {
        "api_key": api_key,
        "frequency": "hourly",
        "data[0]": "value",
        "start": start.strftime("%Y-%m-%dT%H"),   # e.g. 2026-04-13T00
        "end": end.strftime("%Y-%m-%dT%H"),         # e.g. 2026-06-12T00
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "offset": 0,
        "length": 5000,
    }


    BASE_URL = "https://api.eia.gov/v2/electricity/rto/fuel-type-data/data/"

    PAGE_SIZE = 5000
    all_rows = []
    offset = 0
    payload: dict = {}
    while True:
        response = requests.get(
            BASE_URL,
            params={
                **params,
                "offset": offset,
                "length": PAGE_SIZE,
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        batch = payload["response"]["data"]
        if not batch:
            break
        all_rows.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE





    payload["response"]["data"] = all_rows
    payload["response"]["total"] = len(all_rows)

    ingestion_dir = Path("ingestion")
    ingestion_dir.mkdir(exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = ingestion_dir / f"daily-region-sub-ba-data_{timestamp}.json"

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Saved to {output_path}")

    connection = None
    cursor = None

    try:
        connection = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "localhost"),
            database=os.environ["POSTGRES_DB"],
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
            port=os.environ.get("POSTGRES_PORT", "5432"),
        )

        # 2. Create a cursor object to execute SQL commands
        cursor = connection.cursor()

        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        print(f"Successfully connected! PostgreSQL version: {db_version[0]}")

        create_table_query = """
        CREATE TABLE IF NOT EXISTS energy_data_w_fuel_type (
        id SERIAL PRIMARY KEY,
        period TIMESTAMP NOT NULL,
        respondent VARCHAR(50) NOT NULL,
        respondent_name VARCHAR(255) NOT NULL,
        fueltype VARCHAR(10) NOT NULL,
        type_name VARCHAR(255) NOT NULL,
        value NUMERIC(15, 2) NOT NULL,
        value_units VARCHAR(50) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(period, respondent, fueltype)
        );

        CREATE INDEX IF NOT EXISTS idx_fuel_type_period ON energy_data_w_fuel_type(period);
        CREATE INDEX IF NOT EXISTS idx_fuel_type_respondent ON energy_data_w_fuel_type(respondent);
        CREATE INDEX IF NOT EXISTS idx_fuel_type_fueltype ON energy_data_w_fuel_type(fueltype);
        """

        # 4. Execute the SQL command
        cursor.execute(create_table_query)

        upsert_query  = """
        INSERT INTO energy_data_w_fuel_type (
            period, respondent, respondent_name, fueltype, type_name, value, value_units
        ) VALUES %s
        ON CONFLICT (period, respondent, fueltype)
        DO UPDATE SET
            respondent_name = EXCLUDED.respondent_name,
            type_name = EXCLUDED.type_name,
            value = EXCLUDED.value,
            value_units = EXCLUDED.value_units;
            """

        rows = []
        for row in all_rows:
            period = datetime.fromisoformat(row["period"]).replace(tzinfo=timezone.utc)
            rows.append((
                period,
                row["respondent"],
                row["respondent-name"],
                row["fueltype"],
                row["type-name"],
                row["value"],
                row["value-units"],
            ))


        execute_values(cursor, upsert_query, rows, page_size=1000)

        # 5. Commit the transaction to save changes
        connection.commit()
        print("Table 'energy_data_w_fuel_type' synced successfully!")

    except Exception as error:
        print(f"Error while connecting to PostgreSQL: {error}")

    finally:
        # 6. Always close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            print("PostgreSQL connection closed.")


if __name__ == "__main__":
    main()
