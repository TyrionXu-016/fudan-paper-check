# Maker-compatible text extractor.
#
# The application contract is `INPUT.pdf OUTPUT.md`. This lightweight wrapper
# extracts embedded PDF text via poppler so strict mode is not backed by stubs.
FROM debian:bookworm-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends poppler-utils ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY docker/maker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
