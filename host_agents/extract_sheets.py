import gspread, boto3, csv, io, os
from datetime import datetime, timezone

SHEET_URL = "https://docs.google.com/spreadsheets/d/1yeXy-BVed-AsTLvVUg-9wVvc_Ht04YjTi8ECTsjiTrY"

gc = gspread.service_account(filename="gcp_key.json")
sheet = gc.open_by_url(SHEET_URL).sheet1
rows = sheet.get_all_values()

buf = io.StringIO()
csv.writer(buf).writerows(rows)

s3 = boto3.client("s3",
    endpoint_url=os.environ.get("MINIO_ENDPOINT", "http://localhost:9000"),
    aws_access_key_id="minioadmin", aws_secret_access_key="minioadmin123")
key = f"sheets/runs_{datetime.now(timezone.utc):%Y%m%dT%H%M%S}.csv"
s3.put_object(Bucket="bronze", Key=key, Body=buf.getvalue())
print(f"landed {len(rows)-1} rows -> bronze/{key}")