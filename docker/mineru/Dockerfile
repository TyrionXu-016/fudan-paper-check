# MinerU PDF converter (stub)
FROM alpine:3.20
RUN apk add --no-cache bash
COPY docker/mineru-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
