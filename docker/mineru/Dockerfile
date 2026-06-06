# MinerU PDF converter.
#
# The application contract is `INPUT.pdf OUTPUT.md`. Build this image as
# `fudan-pager-mineru` for local quasi-production acceptance.
FROM python:3.12-slim-bookworm
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MINERU_BACKEND=pipeline \
    MINERU_METHOD=auto
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        libglib2.0-0 \
        libgl1 \
        libgomp1 \
        poppler-utils \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -U 'mineru[pipeline]'
RUN pip install --no-cache-dir six
COPY docker/mineru-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
