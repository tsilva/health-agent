#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./sync.sh [profile]
  ./sync.sh --profile <profile>

Runs parser outputs in dependency order:
  1. parselabs
  2. medicalexamsparser
  3. parsehealthlog

If no profile is provided, each parser runs all configured profiles.
EOF
}

profile=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    -p|--profile)
      if [[ $# -lt 2 || -z "$2" ]]; then
        echo "error: --profile requires a value" >&2
        exit 2
      fi
      profile="$2"
      shift 2
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "error: unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      if [[ -n "$profile" ]]; then
        echo "error: profile already set to '$profile'" >&2
        usage >&2
        exit 2
      fi
      profile="$1"
      shift
      ;;
  esac
done

if [[ $# -gt 0 ]]; then
  echo "error: unexpected argument: $1" >&2
  usage >&2
  exit 2
fi

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "error: required command not found on PATH: $1" >&2
    exit 127
  fi
}

run_parser() {
  local command_name="$1"
  shift

  echo
  echo "==> $command_name"
  if ! "$command_name" "$@"; then
    echo "error: $command_name failed; stopping parser sync." >&2
    exit 1
  fi
}

require_command parselabs
require_command medicalexamsparser
require_command parsehealthlog

if [[ -n "$profile" ]]; then
  echo "Running parser sync for profile: $profile"
  run_parser parselabs --profile "$profile"
  run_parser medicalexamsparser --profile "$profile"
  run_parser parsehealthlog --profile "$profile"
else
  echo "Running parser sync for all configured profiles"
  run_parser parselabs
  run_parser medicalexamsparser
  run_parser parsehealthlog
fi

echo
echo "Parser sync complete."
