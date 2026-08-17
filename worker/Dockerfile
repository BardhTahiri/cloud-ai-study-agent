FROM python:3.12-slim

WORKDIR /app

COPY worker/requirements.txt /app/worker/requirements.txt
RUN pip install --no-cache-dir -r /app/worker/requirements.txt

COPY worker /app/worker

ENV PYTHONPATH=/app

EXPOSE 8010

CMD ["uvicorn", "worker.app.api:app", "--host", "0.0.0.0", "--port", "8010"]
