import subprocess, sys
from pathlib import Path
from dagster import asset, Definitions, ScheduleDefinition, define_asset_job

REPO = Path(__file__).resolve().parents[1]

def run(cmd, cwd=REPO):
    res = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    if res.stdout: print(res.stdout)
    if res.stderr: print(res.stderr, file=sys.stderr)
    res.check_returncode()

@asset
def sheets_bronze():
    """Google Sheet snapshot -> MinIO bronze."""
    run([sys.executable, str(REPO / "host_agents" / "extract_sheets.py")])

@asset(deps=[sheets_bronze])
def warehouse():
    """dbt build: bronze -> DuckDB silver/gold."""
    run(["dbt", "build"], cwd=REPO / "dbt" / "drg_dbt")

@asset(deps=[warehouse])
def published_marts():
    """DuckDB marts -> Postgres serving."""
    run([sys.executable, str(REPO / "pipelines" / "publish.py")])

pipeline_job = define_asset_job("nightly_pipeline", selection="*")

nightly = ScheduleDefinition(
    job=pipeline_job,
    cron_schedule="30 18 * * *",
    execution_timezone="America/Indiana/Indianapolis",
)

defs = Definitions(
    assets=[sheets_bronze, warehouse, published_marts],
    jobs=[pipeline_job],
    schedules=[nightly],
)