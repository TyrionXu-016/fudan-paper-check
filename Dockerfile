FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY packages packages
COPY apps apps
COPY config config

RUN sed -i \
        -e 's|http://deb.debian.org/debian|http://mirrors.aliyun.com/debian|g' \
        -e 's|http://security.debian.org/debian-security|http://mirrors.aliyun.com/debian-security|g' \
        /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends docker.io \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --default-timeout=120 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    pydantic pyyaml "httpx[socks]" fastapi "uvicorn[standard]" python-multipart arq redis \
    eval_type_backport pyjwt python-dotenv python-docx reportlab pypdf sqlalchemy jinja2

ENV PYTHONPATH=/app/packages:/app/apps

EXPOSE 8000
