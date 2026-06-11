




#gCO₂/kWh
#Total CO₂ Produced ÷ Electricity Generated

EMISSIONS_FACTORS = {
    "Battery storage": 0.0,
    "Coal": 0.92,
    "Natural Gas": 0.49,
    "Nuclear": 0.012,
    "Petroleum": 0.73,
    "Other": 0.15,
    "Pumped storage": 0.011,
    "Solar": 0.041,
    "Solar with integrated battery storage": 0.041,
    "Hydro": 0.011,
    "Wind": 0.011,
}
 

#Source IPCC 2014 Fifth Assessment Report



#respondent_name
#New England


import os

import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv()


#Query Only Looks at New England at 2 AM


hour = 2
query = f"""
SELECT * FROM public.energy_data_w_fuel_type
WHERE "respondent_name" = 'New England'
AND EXTRACT(HOUR FROM period) = {hour}
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
def row_carbon_emissions(row):
    emissions_factor = EMISSIONS_FACTORS[row["type_name"]]
    return float(row["value"]) * emissions_factor


df = pd.DataFrame(rows, columns=cols)

emissions_values = [row_carbon_emissions(row) for _, row in df.iterrows()]

Emissions_Total = sum(emissions_values)

print(f"At {hour} AM, the carbon intensity is: {Emissions_Total}")




cur.close()
conn.close()
