#!/bin/bash
set -e

cd "$(dirname "$0")/../.."

[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

python ./journal_processing/scripts/extract.py data/journal.docx data/HerbertHollowayJournals.docx
