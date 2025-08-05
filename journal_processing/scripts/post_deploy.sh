#!/bin/bash
set -e

cd "$(dirname "$0")/../.."

# configure the script environment
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt


# build out the pages and data.json
python ./journal_processing/scripts/extract.py \
    data/HerbertHollowayJournals.docx
