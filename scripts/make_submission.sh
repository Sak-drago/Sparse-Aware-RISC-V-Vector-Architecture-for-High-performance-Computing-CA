#!/usr/bin/env bash
# Build the mid-evaluation submission archive: <GroupNo>_<ProjectNo>.zip
# Contents: source, scripts, docs, Makefile, README, results, report sources + PDF,
# and the exact binaries/data used for the demo (so the demo matches the submission).
set -euo pipefail
GROUP=${GROUP:-59}
PROJECT=${PROJECT:-1}
OUT=${OUT:-$PWD/${GROUP}_${PROJECT}.zip}
cd "$(dirname "$0")/.."

# Rebuild binaries and the default results so bin/ and data/ match results/.
make spike > /dev/null
python3 scripts/make_report_tables.py > /dev/null
if [ -f report/midsem_report.tex ]; then
  (cd report && pdflatex -interaction=nonstopmode midsem_report > /dev/null && bibtex midsem_report > /dev/null || true
   pdflatex -interaction=nonstopmode midsem_report > /dev/null && pdflatex -interaction=nonstopmode midsem_report > /dev/null)
fi

rm -f "$OUT"
zip -qr "$OUT" \
  README.md Makefile src scripts docs examples results bin data \
  report/midsem_report.tex report/midsem_report.pdf report/refs.bib report/tables report/figures \
  -x '*/__pycache__/*' 'data/.params'
echo "wrote $OUT ($(du -h "$OUT" | cut -f1))"
unzip -l "$OUT" | tail -1
