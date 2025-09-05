# Herbert Holloway's Journal

## Introduction

I have an ongoing personal project to study and publish information about
my Great, Great Uncle based on his Journals. I am slowly building things out
into a web site:

https://HerbertHolloway.org

So, I thought I'd take the opportunity to demonstrate some Python coding - 
something I should probably do after spending 30 years focusing mainly on Perl.

I've used [Jekyll](https://jekyllrb.com/) to build out the site. Never used it
before, but got everything built and working in less than a day, and figured
it would be a good example of learning a new stack. The site is built out using
a github deploy action.

I have included a zip of the core of the Jekyll site in this file:

    data/JekyllWebSite.zip

just in case you're curious. I've kept the site simple, so not much to see except
for the book page navigation (that works in desktop and on mobile).

Note: deskewing and stitching the original scans of the journal has been made generic
and moved to [its own repo](https://github.com/cliveholloway/document_digitizer/)

## Features in this repo

### extract

Process the transcript of the journal that's in a docx file:

- parse the docx file 
- create individual HTML pages for a browse option
- create page text files to train an LLM

There is currently a bug in this code ATM that doesn't create blank pages, so images
are currently appended to incorrect pages.

### ocr

Process scans of images from the original journal:

- batch process via Anthropic's API
- review output and tweak prompt instructions to improve OCR 
- commit updated prompt instructions and run again
- when number of errors is very small, make this the final implementation
  and compare against the manually transcribed version for diffs

The goal of this is to show how I _could_ have created the HTML and text from
the original images. When I first scanned them, an AI agent wasn't able
to OCR them very well, so I had them transcribed manually, but this is a good
demo of how to achieve the same goal via an LLM API.

## Notes

I looked at auto-parsing out the images too, but hit some complications with the way
the images were originally added, so I am only creating the HTML and comments dynamically.
The images are fixed anyway, so the 10 minutes it took me to manually create the
assets made a lot more sense than trying to hack through XML parsing. I'll fix this soon

This __is__ a work in progress, so until this file is cleaned up, assume docs may not
match code, and code is incomplete.

For more information about my general experience and references, please see:

https://cliveholloway.net/2025

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

See the Jekyll zip file for details of how the site is built (separate, private repo)

txt is going to be used to train the LLM for questions - TODO

### Image OCR

Using Anthropic's API for Claude, I batch process the source images into txt files
