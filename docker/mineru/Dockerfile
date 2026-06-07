# MinerU PDF converter.
#
# The application contract is `INPUT.pdf OUTPUT.md`. Build this image as
# `fudan-pager-mse-mineru` for the isolated MSE backend deployment.
FROM python:3.12-slim-bookworm
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MINERU_BACKEND=pipeline \
    MINERU_METHOD=auto
RUN sed -i \
        -e 's|http://deb.debian.org/debian|http://mirrors.aliyun.com/debian|g' \
        -e 's|http://security.debian.org/debian-security|http://mirrors.aliyun.com/debian-security|g' \
        /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        libglib2.0-0 \
        libgl1 \
        libgomp1 \
        poppler-utils \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -U -i https://pypi.tuna.tsinghua.edu.cn/simple 'mineru[pipeline]'
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple six
COPY docker/mineru-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
