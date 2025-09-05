#Quality analysis

The odt files in this directory show the output with the number of
errors (highlighted) for the opus and sonnet models (haiku was not good enough).

I first did a run with no hints, then took common mistakes across the
3 models and submitted them as hints with the API request.

This definitelty helped quite a bit. I am not optimizing this further
because I have no need for this, but I feel I have demonstrated an approach
that would help scan, as accurately as possible, the raw pages by the API.

With the hints, most of the errors are punctuation, which is going to be
challenging in this test.

I have left in some test pages so you can run the API requests yourself.

Note: before you start, you must set an Anthropic API key in the environment
variable `ANTHROPIC_API_KEY`

```bash
# run with the hjints enabled
herbert ocr data/test_scans
```

The OCR's pages are in `output/ocr_pages

Move the hints out of the way and run without them to see the difference.

``
mv data/ocr_hints data/ocr_hints.bak
herbert ocr data/test_scans
```
