FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY packages packages
COPY apps apps
COPY config config

RUN pip install --no-cache-dir --default-timeout=120 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    pydantic pyyaml httpx fastapi "uvicorn[standard]" python-multipart arq redis \
    eval_type_backport pyjwt python-docx reportlab docker

ENV PYTHONPATH=/app/packages:/app/apps

EXPOSE 8000
