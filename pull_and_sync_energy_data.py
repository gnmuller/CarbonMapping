import json
import os
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
import requests
from dotenv import load_dotenv

load_dotenv()


def main():
    api_key = os.environ["EIA_API_KEY"]

    response = requests.get(
        "https://api.eia.gov/v2/electricity/rto/fuel-type-data/data/",
        params={
            "api_key": api_key,
            "frequency": "hourly",
            "data[0]": "value",
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "offset": 0,
            "length": 5000,
        },
    )
    response.raise_for_status()

    data = response.json()

    ingestion_dir = Path("ingestion")
    ingestion_dir.mkdir(exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = ingestion_dir / f"daily-region-sub-ba-data_{timestamp}.json"

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

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

        insert_query = """
            INSERT INTO energy_data_w_fuel_type (
                period, respondent, respondent_name, fueltype, type_name, value, value_units
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (period, respondent, fueltype) DO NOTHING
            """

        rows = []
        for row in data["response"]["data"]:
            tuple_row = (
                f"{row['period']}:00:00",
                row["respondent"],
                row["respondent-name"],
                row["fueltype"],
                row["type-name"],
                row["value"],
                row["value-units"],
            )
            rows.append(tuple_row)

        cursor.executemany(insert_query, rows)
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
