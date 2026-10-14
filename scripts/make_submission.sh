#!/usr/bin/env bash
# Build the mid-evaluation submission archive: <GroupNo>_<ProjectNo>.zip
# Contents: source, scripts, docs, Makefile, README, RESULTS, results,
# and the exact binaries/data used for the demo (so the demo matches the submission).
set -euo pipefail
GROUP=${GROUP:-59}
PROJECT=${PROJECT:-1}
OUT=${OUT:-$PWD/${GROUP}_${PROJECT}.zip}
cd "$(dirname "$0")/.."

# Rebuild binaries and the default results so bin/ and data/ match results/.
make spike > /dev/null

rm -f "$OUT"
zip -qr "$OUT" \
  README.md RESULTS.md Makefile src scripts docs examples results bin data \
  -x '*/__pycache__/*' 'data/.params'
echo "wrote $OUT ($(du -h "$OUT" | cut -f1))"
unzip -l "$OUT" | tail -1
