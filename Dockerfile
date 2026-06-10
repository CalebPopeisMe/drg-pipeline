FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
ENV DAGSTER_HOME=/opt/dagster
EXPOSE 3000
CMD ["dagster", "dev", "-f", "pipelines/dagster_defs.py", "-h", "0.0.0.0", "-p", "3000"]