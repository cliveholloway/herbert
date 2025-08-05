#!/bin/bash
set -e

cd "$(dirname "$0")/../.."

[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# build out the pages
python ./journal_processing/scripts/extract.py \
    data/HerbertHollowayJournals.docx

# update the build dir (used by the website)
rm -rf ~/build
mv ./journal_processing/build ~/build
