import argparse
from herbert.commands import extract
# future: from herbert.commands import batch, etc.


def main():
    parser = argparse.ArgumentParser(
        prog="herbert",
        description="Herbert journal processing toolkit"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- extract subcommand ---
    extract_parser = subparsers.add_parser(
        "extract", help="Extract pages from DOCX into HTML/TXT/JSON"
    )
    extract_parser.add_argument("input_docx", help="Path to the input .docx file")
    extract_parser.add_argument("output_dir", help="Directory where output is written")
    extract_parser.set_defaults(func=extract.run)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

