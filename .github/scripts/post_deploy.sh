#!/bin/bash
set -e

cd "$(dirname "$0")/../.."

# configure the script environment
[ -d venv ] || python3 -m venv venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .

# build out the pages and data.json
herbert extract data/HerbertHollowayJournals.docx
