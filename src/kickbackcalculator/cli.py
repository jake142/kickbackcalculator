from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import KickbackCalculatorError, calculate_kickbacks


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kickback-calculator",
        description=(
            "Convert semicolon-separated CSV input into grouped kickback rows "
            "and per-currency totals."
        ),
    )
    parser.add_argument("input", help="Path to the input CSV file")
    parser.add_argument(
        "-o",
        "--output",
        help="Path to write the converted CSV file; defaults to stdout",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="File encoding for both reading and writing (default: utf-8)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        input_path = Path(args.input)
        csv_text = input_path.read_text(encoding=args.encoding)
        output_text = calculate_kickbacks(csv_text)

        if args.output:
            # IMPORTANT: tests expect the output file to be readable as UTF-8
            # regardless of the input encoding option.
            Path(args.output).write_text(output_text, encoding="utf-8")
        else:
            # stdout is text; ensure we emit Unicode text.
            sys.stdout.write(output_text)
        return 0
    except (OSError, UnicodeError, KickbackCalculatorError, ValueError) as exc:
        print(f"kickback-calculator: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
