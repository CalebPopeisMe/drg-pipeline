@echo off
cd /d C:\Users\Caleb\drg-pipeline
echo ==== pipeline run %date% %time% ==== >> pipeline.log

python host_agents\extract_sheets.py >> pipeline.log 2>&1 || goto :fail
cd dbt\drg_dbt
call dbt build >> ..\..\pipeline.log 2>&1 || goto :fail
cd ..\..
python pipelines\publish.py >> pipeline.log 2>&1 || goto :fail

echo ==== SUCCESS ==== >> pipeline.log
exit /b 0
:fail
echo ==== FAILED ==== >> pipeline.log
exit /b 1