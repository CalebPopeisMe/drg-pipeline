What is my true, validated Merits-per-hour trend across patches — and am I improving faster than the playerbase


# DRG: Rogue Core — Run Analytics Pipeline

A local-first ELT pipeline that ingests my Deep Rock Galactic: Rogue Core run history from multiple sources, transforms it into a dimensional warehouse, and serves KPIs (merits/hour, completion rate, failure taxonomy) to BI dashboards. Built as a data engineering portfolio project: every layer is intentionally the kind of component a production data platform uses, scaled to a single-player problem.

**Headline question:** What is my true, validated merits-per-hour trend across patches — and am I improving faster than the playerbase?

## Architecture (current)

```
Google Sheet ──> extract_sheets.py ──> MinIO (bronze) ──> dbt + DuckDB ──> publish.py ──> Postgres ──> Metabase
 (run log)         (Python, host)      (raw snapshots)    (silver/gold)     (Python)      (serving)    (dashboards)
```

- **Sources:** a structured Google Sheet where each run is logged manually (timestamp, class, mission type, outcome, failure cause, merits, duration, fun rating).
- **Extract & load:** `host_agents/extract_sheets.py` pulls full sheet snapshots via the Sheets API (gspread) and lands timestamped CSVs in a MinIO bucket via the S3 API (boto3). Snapshot-style loads keep the extractor idempotent.
- **Storage:** MinIO (S3-compatible object store) holds immutable raw files — the bronze layer. Nothing downstream ever mutates bronze.
- **Transform:** dbt (dbt-duckdb adapter) builds the warehouse in a local DuckDB file. Staging reads bronze CSVs directly from MinIO via DuckDB's httpfs/S3 support, types all columns, normalizes empty strings to NULLs, and dedupes overlapping snapshots with a window function (latest file wins). Marts aggregate to KPI tables. All models materialize as tables.
- **Serving:** `pipelines/publish.py` attaches Postgres from DuckDB (postgres extension) and replaces the mart tables — an idempotent publish. Postgres is the serving database because DuckDB is single-writer/embedded and shouldn't back a BI server.
- **BI:** Metabase reads Postgres. Power BI Desktop can connect to the same database at localhost:5432.
- **Infra:** MinIO, Postgres, and Metabase run via Docker Compose with named volumes for persistence. Transform tooling (dbt/DuckDB) and extractors run on the host for now.

### Running the pipeline

```
python host_agents\extract_sheets.py     # Sheet -> bronze
cd dbt\drg_dbt && dbt build && cd ..\..  # bronze -> warehouse
python pipelines\publish.py              # warehouse -> Postgres
```

Stack up/down: `docker compose up -d` / `docker compose down` (volumes persist).

## Architecture (planned)

The same spine, with more sources, orchestration, and validation:

- **Orchestration:** Dagster (containerized) replaces manual/scheduled runs — schedules for pull-based sources, sensors on bronze, retries, lineage, and run history.
- **Ingest API:** a FastAPI service in the compose stack receives POSTs from host agents and writes to bronze, decoupling host-side watchers from storage.
- **Save-file CDC:** a Windows watchdog agent snapshots Rogue Core's save file after each run; diffing GVAS snapshots yields exact merit/XP deltas — a ground-truth completeness check on the manually logged data.
- **Screenshot OCR:** end-of-run screenshots are OCR'd into a second independent measurement of each run; a reconciliation rule resolves disagreements with the sheet and logs discrepancies.
- **External APIs:** Steam Web API polled daily for playtime (a capture-rate audit on the fact table) and global achievement percentages (population benchmark); patch-notes RSS feeds the patch dimension.
- **Reference data:** wiki-scraped upgrade/class/mission dimensions, tracked as SCD Type 2 via dbt snapshots so KPIs stay comparable across balance patches.
- **Quality & CI:** dbt tests (not-null, accepted values, uniqueness) and a GitHub Actions workflow running `dbt build` against seed data on every push.
- **Analysis:** Jupyter notebooks over the DuckDB warehouse — risk-adjusted merits/hour by mission type, failure-cause breakdowns, push-vs-extract expected-value modeling.

## Notes

- Credentials in `docker-compose.yml` are hardcoded for local development only; all services bind to a single-user machine and nothing is exposed publicly. Secrets that matter (the GCP service-account key) are gitignored.
- The warehouse file (`warehouse/*.duckdb`) and dbt artifacts are build outputs and are not committed; `dbt build` reconstructs the warehouse from bronze.
- Designed for intermittent operation: the PC is not always on, so all loads are snapshot- or watermark-based and safe to re-run late. Missed Steam polls leave benchmark gaps, never pipeline failures.
