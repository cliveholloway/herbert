# Herbert Holloway's Journal

This repo is my first coding in Python, after 29 years of focusing on Perl.

For speed, I have written this using "vibe coding" followed by manual tweaking
as needed. This is about 3 days work in total, spread over a week.

The goal is to create web site assets, using Python, to showcase my Great,
Great Uncle's journals that he wrote in 1918. A separate (private) repo
takes the output from this code and uses it to serve the web site:

https://HerbertHolloway.org

## Features

For the original scans of the journal:

- convert TIF images to PNG
- deskew images
- stitch images together

For the transcript of the journal that's in a docx file:

- parse the docx file 
- create individual HTML pages for a browse option
- create page text files to train an LLM

## Notes

This repo only includes a few sample images and a few pages of the journal

I looked at auto-parsing out the images too, but hit some complications with the way
the images were originally added, so I am only creationg the HTML and comments dynamically.
The images are fixed anyway, so the 10 minutes it took me to manually create the
assets made a lot more sense than trying to hack through XML parsing.

This will probably not be a complete project, but it should show how quickly I can
learn and implement a new stack via "vibe coding" and by leveraging my understanding
of design patterns from Perl. Much as I love Perl, I get that most of the industry
has a not so good view of it, and it's days as a commercial language are numbered.

For more information about my general experience and references, please see:

https://cliveholloway.net/2025

## Running the code

After you've checked out the repo, you can look at the example images that were created
while testing (and committed here for visibility)

    # set up your env
    python3 -m venv .venv
    source .venv/bin/activate
    pip install poetry

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

For the journal processing, I have included a few sample pages, some with images:

    python3 journal_processing/scripts/extract.py data/journal.docx

After you run the script, you'll see the HTML pages in the dir journal_processing/build/pages
and the comments stored in journal_processing/build/data.json  (this is used to add the comments
back into into the web pages).

Raw text is placed in journal_processing/build/txt (used to train the LLM)

