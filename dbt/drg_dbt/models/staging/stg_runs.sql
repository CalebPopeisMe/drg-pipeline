select
    cast(played_at as timestamp)  as played_at,
    class,
    mission_type,
    outcome,
    nullif(failure_cause, '')     as failure_cause,
    cast(merits as integer)       as merits,
    cast(duration_min as integer) as duration_min,
    cast(fun as integer)          as fun
from read_csv_auto('s3://bronze/sheets/runs_*.csv',
                   union_by_name = true,
                   filename = true)
qualify row_number() over (
    partition by played_at
    order by filename desc
) = 1