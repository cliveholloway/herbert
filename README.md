# Herbert Holloway's Journal

## Introduction

I have an ongoing personal project to study and publish details about
my Great, Great Uncle's life based on his Journals. I am slowly building
things out into a web site:

https://HerbertHolloway.org

The website is built out from the docx file included in this repo, by code that
builds out HTML and text pages, and creates a JSON file with all the copmments in.

I decided to write the code for this in Python to show I can pick up new stacks - 
something I should probably do after spending 30 years focusing mainly on Perl!

I've also used [Jekyll](https://jekyllrb.com/) (ruby site templates) to build
out the site. Never used it before, but got everything built and working in less
than a day. The site is built out on merge to main using a github deploy action.

The web site repo is private, but here's a few key pointers about it:

- the data generated here is used by a Javascript controller to manage navigating the parsed journal
- the text files are used to populate the search engine
- comments are injected on the fly from the data parsed into data.json
- a Python flask app controls the search and email sign up code

Note: deskewing and stitching the original scans of the journal has been made generic
and moved to [its own repo](https://github.com/cliveholloway/document_digitizer/).
This code is generic enough that it deserves to be in a standalone repo.

## Features in this repo

### extract

Process the transcript of the journal that's in a docx file:

- parse the docx file 
- create individual HTML pages for a browse option
- create page text files to train an LLM
- extract comments and store them in a JSON file for front end rendering

### OCR

Process scans of images from the original journal:

- batch process via Anthropic's API
- review output and tweak prompt instructions to improve OCR 
- commit updated prompt instructions and run again
- when number of errors is very small, make this the final implementation
  and compare against the manually transcribed version for diffs

The goal of this is to show how I _would_ have created the HTML if I was starting today.
When I first started working on this journal a couple of years ago, the quality of
AI OCR was nowhere near where it is today, so I had them transcribed manually. 

Out of curiosity, I wondered how easy it would be to do, so I took the time to flesh
out a demo of how I would achieve the same goals today via LLM API calls.

## Notes

I looked at auto-parsing out the images out of the docx file as well when building the
web pages, but I hit some complications with the way the images were originally added
to the docx file, so I am only creating the HTML and comments dynamically.  The images
are fixed anyway, so the 10 minutes it took me to manually create the assets made a
lot more sense than trying to hack through XML parsing. 

## Running the code

### env set up

After you've checked out the repo, you can run the individual scripts to see them in
action.

    # set up your env
    python3 -m venv venv

    # enter the env and install dependencies
    source venv/bin/activate
    pip install -e .

### Journal parsing

For the journal processing, run this script to build out the web pages:

    herbert extract data/HerbertHollowayJournals.docx

After you run the script, you'll see the text files, HTML page snippits and data.json in the dir;

    output

The data.json file is used to manage the comment additions to the pages.

The pages and data.json are added to the web site via a build action in the web site repo.

txt is going to be used to train the LLM for questions on the web site.

### Image OCR

Using Anthropic's API for Claude, I batch process the source images into txt files using both
the Sonnet and Opus models.

I've been playing around with a few prompt structures, and have found that adding "hint" images
to help with the cursive that the quality of the OCR improves, but it would still need
a lot of manual review before I would trust it to completely transcribe. I do think it's
a useful demo as is though.

To run this, you will need an anthropic API key, and you must set it in the `ANTHROPIC_API_KEY`
environment variable.

```bash
export ANTHROPIC_API_KEY=...
```

To process a directory of images, run:

    herbert ocr data/test_scans

I am not fleshing this demo out further right now, since I already have a transcript, but wanted to
demonstrate the approach I _would_ take if starting today. No doubt if this was needied for a
commercial application I would refine the prompt and hints, and compare output from each model
to attempt to correct errors over several iterations.
