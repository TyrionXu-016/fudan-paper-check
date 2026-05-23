FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY packages packages
COPY apps apps
COPY config config
COPY samples samples

RUN pip install --no-cache-dir pydantic pyyaml httpx fastapi "uvicorn[standard]" python-multipart arq redis eval_type_backport pyjwt

ENV PYTHONPATH=/app/packages:/app/apps

EXPOSE 8000
