from herbert.ocr import run_ocr

def run(args):
    """CLI wrapper for `herbert ocr`."""
    # pass second argument if present
    if hasattr(args, "label") and args.label:
        run_ocr(args.source_dir, args.label)
    else:
        run_ocr(args.source_dir)

