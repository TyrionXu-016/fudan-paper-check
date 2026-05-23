# Maker PDF converter (stub)
# Replace with actual Maker CLI/image in production.
FROM alpine:3.20
RUN apk add --no-cache bash
COPY docker/maker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
