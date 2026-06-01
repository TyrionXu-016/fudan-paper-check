#!/bin/sh
# Usage: mineru INPUT.pdf OUTPUT.md
INPUT="$1"
OUTPUT="$2"
echo "# Converted by MinerU stub from $(basename "$INPUT")" > "$OUTPUT"
echo "" >> "$OUTPUT"
echo "<table><tr><td>stub</td></tr></table>" >> "$OUTPUT"
