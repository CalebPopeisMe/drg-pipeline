import duckdb, os
pg_host = os.environ.get("PG_HOST", "localhost")

con = duckdb.connect("warehouse/drg.duckdb")
con.sql("INSTALL postgres; LOAD postgres;")
con.sql(f"""
    ATTACH 'host={pg_host} port=5432 dbname=warehouse user=drg password=drgpass'
    AS pg (TYPE POSTGRES)
""")
con.sql("CREATE OR REPLACE TABLE pg.public.mart_merits_per_hour AS SELECT * FROM mart_merits_per_hour")
n = con.sql("SELECT count(*) FROM pg.public.mart_merits_per_hour").fetchone()[0]
print(f"published mart_merits_per_hour -> postgres ({n} rows)")