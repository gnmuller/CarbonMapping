from dagster import Definitions, load_assets_from_modules
from dagster_dbt import DbtCliResource

from carbonmapping_dagster.assets import eia_ingestion
from carbonmapping_dagster.assets import carbonmapping_dbt_assets, dbt_project

all_assets = [
    *load_assets_from_modules([eia_ingestion]),
    carbonmapping_dbt_assets,
]

defs = Definitions(
    assets=all_assets,
    resources={"dbt": DbtCliResource(project_dir=dbt_project)},
)