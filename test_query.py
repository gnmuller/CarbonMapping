import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

query = """

SELECT * FROM energy_data_w_fuel_type
WHERE type_name = 'Solar'
AND EXTRACT(HOUR FROM period) BETWEEN 17 AND 23;
"""


conn = psycopg2.connect(
    host=os.environ.get("POSTGRES_HOST", "localhost"),
    database=os.environ["POSTGRES_DB"],
    user=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    port=os.environ.get("POSTGRES_PORT", "5432"),
)
cur = conn.cursor()
cur.execute(query)
rows = cur.fetchall()
cols = [d[0] for d in cur.description]
print("Columns:", cols)
print("Row count:", len(rows))
for row in rows[:20]:
    print(row)
if len(rows) > 20:
    print(f"... and {len(rows) - 20} more rows")
cur.close()
conn.close()
