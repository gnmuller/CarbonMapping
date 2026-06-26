# orchestra/carbonmapping_dagster/assets/dbt_assets.py
from pathlib import Path

from dagster import AssetExecutionContext
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

# orchestra/carbonmapping_dagster/assets/ -> repo root
REPO_ROOT = Path(__file__).resolve().parents[3]
DBT_PROJECT_DIR = REPO_ROOT / "dbt"

dbt_project = DbtProject(
    project_dir=DBT_PROJECT_DIR,
    profiles_dir=DBT_PROJECT_DIR,  # Profiles.yml is here
)
dbt_project.prepare_if_dev()  # auto-parse manifest in dev


@dbt_assets(manifest=dbt_project.manifest_path, project=dbt_project)
def carbonmapping_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()