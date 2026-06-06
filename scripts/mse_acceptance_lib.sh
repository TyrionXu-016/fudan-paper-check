#!/usr/bin/env bash

mse_is_strict_mode() {
  case "${MSE_ALLOW_MOCK_FALLBACK:-1}" in
    0|false|FALSE|no|NO) return 0 ;;
    *) return 1 ;;
  esac
}

mse_pick_submission_file() {
  local root="$1"
  if mse_is_strict_mode; then
    if [[ -z "${MINERU_TEST_PDF:-}" || ! -f "${MINERU_TEST_PDF:-}" ]]; then
      echo "严格模式需要设置 MINERU_TEST_PDF=/path/to/public-thesis.pdf" >&2
      return 1
    fi
    echo "$MINERU_TEST_PDF"
    return 0
  fi
  find "$root/samples" -name '*_maker.md' 2>/dev/null | head -1
}

mse_submission_filename() {
  local path="$1"
  case "${path##*.}" in
    pdf|PDF) basename "$path" ;;
    *) echo "paper.pdf" ;;
  esac
}

mse_submission_mime() {
  local path="$1"
  case "${path##*.}" in
    pdf|PDF) echo "application/pdf" ;;
    *) echo "application/pdf" ;;
  esac
}
