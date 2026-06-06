#!/bin/sh
set -eu

INPUT="${1:?Usage: maker INPUT.pdf OUTPUT.md}"
OUTPUT="${2:?Usage: maker INPUT.pdf OUTPUT.md}"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

mkdir -p "$(dirname "$OUTPUT")"

PAGE_ARGS=""
START_PAGE="${MAKER_START_PAGE:-${MINERU_START_PAGE:-}}"
END_PAGE="${MAKER_END_PAGE:-${MINERU_END_PAGE:-}}"
if [ -n "$START_PAGE" ]; then
  case "$START_PAGE" in
    *[!0-9]*)
      echo "MAKER_START_PAGE must be a non-negative integer" >&2
      exit 2
      ;;
  esac
  PAGE_ARGS="$PAGE_ARGS -f $((START_PAGE + 1))"
fi
if [ -n "$END_PAGE" ]; then
  case "$END_PAGE" in
    *[!0-9]*)
      echo "MAKER_END_PAGE must be a non-negative integer" >&2
      exit 2
      ;;
  esac
  PAGE_ARGS="$PAGE_ARGS -l $((END_PAGE + 1))"
fi

# shellcheck disable=SC2086
pdftotext -layout $PAGE_ARGS "$INPUT" "$TMP"

if [ ! -s "$TMP" ]; then
  echo "maker-compatible extraction produced no text" >&2
  exit 2
fi

{
  echo "# Converted by Maker-compatible text extractor from $(basename "$INPUT")"
  echo
  cat "$TMP"
} > "$OUTPUT"
