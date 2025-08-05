# Herbert Holloway's Journal

## Introduction

I have an ongoing personal project to study and publish information about
my Great, Great Uncle based on his Journals. I am slowly building things out
into a web site:

https://HerbertHolloway.org

So, I thought I'd take the opportunity to plow through some Python coding - 
something I should probably do after spending 29 years focusing on Perl.

For speed, I have written most iof this dcode using "vibe coding", followed by
manual tweaking as needed. This is about a week's work in total.

I've used [Jekyll](https://jekyllrb.com/) to build out the site. Never used it
before, but got everything built and working in less than a day, and figured
it would be a good example of learning a new stack. The site is built out using
a githubv deploy action.

I have included a zip of the core of the Jekyll site in this file:

    data/JekyllWebSite.zip

just in case you're curious. I've kept the site simple, so not much to see except
for the book page navigation (that works in desktop and on mobile).

## Features in this repo

For the original scans of the journal:

- convert TIF images to PNG
- deskew images
- stitch images together (TODO - steep learning curve here)

For the transcript of the journal that's in a docx file:

- parse the docx file 
- create individual HTML pages for a browse option
- create page text files to train an LLM

## Notes

I looked at auto-parsing out the images too, but hit some complications with the way
the images were originally added, so I am only creating the HTML and comments dynamically.
The images are fixed anyway, so the 10 minutes it took me to manually create the
assets made a lot more sense than trying to hack through XML parsing.

It looks like blank pages were omitted from the conversion though, so I do need to rename a
bunch of the images so that they render on the correct pages.

This will probably not be a complete project, but it should show how quickly I can
learn and implement a new stack via "vibe coding" and by leveraging my understanding
of design patterns from Perl. Much as I love Perl, I get that most of the industry
has a not so good view of it, and it's days as a commercial language are numbered.

For more information about my general experience and references, please see:

https://cliveholloway.net/2025

## Running the code

### env set up

After you've checked out the repo, you can run the individual scripts to see them in
action.

    # set up your env
    python3 -m venv .venv
    source .venv/bin/activate
    pip install poetry
    poetry install

### Image processing

For the image processing code, it's broken into 3 scripts. Each batch processes
a directory of images. I have included scans of the first 2 pages in the repo

    # convert the tif images to png images
    python3 image_processing/scripts/1_batch_convert.py \
        data/tif_flatbed_scans image_processing/build/png_scans 

Converted png images are in image_processing/build/png_scans

    # deskew the png_images
    python3 image_processing/scripts/2_image_deskew.py \
        image_processing/build/png_scans  image_processing/build/deskewed_scans 

Deskewed images are in image_processing/build/deskewed_scans

    # TODO - get stitching fixed and put instructions in here

### Journal parsing

For the journal processing, run this script to build out the web pages:

    python3 journal_processing/scripts/extract.py \
        data/HerbertHollowayJournals.docx

After you run the script, you'll see the HTML pages and data.json in the dir;

    journal_processing/build

The data.json file is used to manage the comment additions to the pages.

Raw text is placed in journal_processing/build/txt (used to train the LLM - TODO) 
