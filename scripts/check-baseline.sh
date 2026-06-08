#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
FLUSHOT="$ROOT_DIR/flushot.py"

if grep -Fq 'http://www.cdc.gov/flu/weekly/' "$FLUSHOT"; then
  printf '%s\n' "flushot.py must not use the plain-HTTP CDC flu endpoint." >&2
  exit 1
fi

if ! grep -Fq 'https://www.cdc.gov/flu/weekly/' "$FLUSHOT"; then
  printf '%s\n' "flushot.py must use the HTTPS CDC flu endpoint." >&2
  exit 1
fi

printf '%s\n' "Flu shot data baseline checks passed."
