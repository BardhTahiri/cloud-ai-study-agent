FROM node:22-bookworm-slim AS codex

ARG CODEX_VERSION=latest
RUN npm install --global "@openai/codex@${CODEX_VERSION}"

FROM python:3.12-slim-bookworm

COPY --from=codex /usr/local/bin/node /usr/local/bin/node
COPY --from=codex /usr/local/bin/codex /usr/local/bin/codex
COPY --from=codex /usr/local/lib/node_modules/@openai/codex /usr/local/lib/node_modules/@openai/codex

WORKDIR /app

COPY worker/requirements.txt /app/worker/requirements.txt
RUN pip install --no-cache-dir -r /app/worker/requirements.txt

COPY worker /app/worker

ENV PYTHONPATH=/app
ENV CODEX_HOME=/codex-auth

EXPOSE 8010

CMD ["uvicorn", "worker.app.api:app", "--host", "0.0.0.0", "--port", "8010"]
