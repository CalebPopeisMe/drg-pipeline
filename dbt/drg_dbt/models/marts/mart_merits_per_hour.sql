select
    mission_type,
    round(avg(merits * 60.0 / duration_min)) as merits_per_hour,
    round(avg(case when outcome = 'extracted' then 1.0 else 0.0 end) * 100) as completion_pct,
    count(*) as n_runs
from {{ ref('stg_runs') }}
group by mission_type
order by merits_per_hour desc