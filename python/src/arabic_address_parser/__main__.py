import argparse
import json
import sys

from . import __version__, format_address, parse, similarity


def main(argv=None):
    ap = argparse.ArgumentParser(prog="arabic-address-parser", description="Parse an Arabic address into components.")
    ap.add_argument("address", nargs="*", help="address text (reads stdin when omitted)")
    ap.add_argument("--default-country", help="ISO code used when the text does not mention a country, e.g. EG")
    ap.add_argument("--format", choices=["ar", "en"], help="print one canonical line instead of JSON")
    ap.add_argument("--compare", metavar="OTHER", help="print the similarity score against OTHER")
    ap.add_argument("--version", action="version", version=__version__)
    args = ap.parse_args(argv)
    text = " ".join(args.address) if args.address else sys.stdin.read()
    if args.compare is not None:
        print(similarity(text, args.compare))
        return 0
    result = parse(text, default_country=args.default_country)
    if args.format:
        print(format_address(result, args.format))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
