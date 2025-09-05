import argparse
import sys

from herbert.commands import extract, ocr


def main():
    parser = argparse.ArgumentParser(
        prog="herbert",
        description="Herbert Holloway Journal Processing CLI",
    )
    subparsers = parser.add_subparsers(dest="command")

    # extract subcommand
    p_extract = subparsers.add_parser("extract", help="Extract data")
    p_extract.add_argument("source_file", help="Path to input .docx file")
    p_extract.set_defaults(func=extract.run)

    # ocr subcommand
    p_ocr = subparsers.add_parser("ocr", help="Run OCR on scanned pages")
    p_ocr.add_argument("source_dir", help="Directory containing images & prompt.txt")
    p_ocr.add_argument(
        "label",
        nargs="?",
        default="",
        help="Optional label appended to output filenames (e.g. 'test1')",
    )
    p_ocr.set_defaults(func=ocr.run)

    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()

