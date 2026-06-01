#!/bin/sh
# Usage: maker INPUT.pdf OUTPUT.md
INPUT="$1"
OUTPUT="$2"
echo "# Converted by Maker stub from $(basename "$INPUT")" > "$OUTPUT"
echo "" >> "$OUTPUT"
echo "Replace this stub with real Maker conversion." >> "$OUTPUT"
