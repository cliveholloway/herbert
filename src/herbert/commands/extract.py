from herbert.extractor import extract_docx


def run(args):
    """Run the extract command"""
    extract_docx(args.source_file)  # input docx
