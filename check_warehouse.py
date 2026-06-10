import duckdb
con = duckdb.connect("warehouse/drg.duckdb")
print(con.sql("select table_name, table_type from information_schema.tables"))
print(con.sql("select * from mart_merits_per_hour"))