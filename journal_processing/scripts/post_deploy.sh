#!/bin/bash
set -e

cd "$(dirname "$0")/.."  # adjust to project root if needed

[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

python ./journal_processing/scripts/extract.py data/journal.docx

mkdir -p ../www/herbertholloway.org/public_html/pages
cp ./journal_processing/build/pages/* ../www/herbertholloway.org/public_html/pages/
cp ./journal_processing/build/data.json ../www/herbertholloway.org/public_html/
