from herbert.extractor import extract_docx


def run(args):
    """CLI wrapper for `herbert extract`."""
    extract_docx(args.input_docx)
