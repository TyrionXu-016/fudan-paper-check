#!/bin/sh
set -eu

INPUT="${1:?Usage: mineru INPUT.pdf OUTPUT.md}"
OUTPUT="${2:?Usage: mineru INPUT.pdf OUTPUT.md}"
WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

mkdir -p "$(dirname "$OUTPUT")"

PAGE_ARGS=""
if [ -n "${MINERU_START_PAGE:-}" ]; then
  case "$MINERU_START_PAGE" in
    *[!0-9]*)
      echo "MINERU_START_PAGE must be a non-negative integer" >&2
      exit 2
      ;;
  esac
  PAGE_ARGS="$PAGE_ARGS -s $MINERU_START_PAGE"
fi
if [ -n "${MINERU_END_PAGE:-}" ]; then
  case "$MINERU_END_PAGE" in
    *[!0-9]*)
      echo "MINERU_END_PAGE must be a non-negative integer" >&2
      exit 2
      ;;
  esac
  PAGE_ARGS="$PAGE_ARGS -e $MINERU_END_PAGE"
fi

# shellcheck disable=SC2086
if ! mineru \
  -p "$INPUT" \
  -o "$WORKDIR" \
  -b "${MINERU_BACKEND:-pipeline}" \
  -m "${MINERU_METHOD:-auto}" \
  $PAGE_ARGS \
  --client-side-output-generation true; then
  # shellcheck disable=SC2086
  mineru \
    -p "$INPUT" \
    -o "$WORKDIR" \
    -b "${MINERU_BACKEND:-pipeline}" \
    -m "${MINERU_METHOD:-auto}" \
    $PAGE_ARGS
fi

MD_FILE="$(find "$WORKDIR" -type f -name '*.md' | sort | head -1)"
if [ -z "$MD_FILE" ] || [ ! -s "$MD_FILE" ]; then
  echo "MinerU produced no markdown output" >&2
  exit 2
fi

cp "$MD_FILE" "$OUTPUT"
