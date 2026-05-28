# KickbackCalculator by packr.build
A tiny Python CLI and library for turning semicolon CSV rows into grouped kickback totals.

## Table of Contents
- [Why this package](#why-this-package)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Quick start](#quick-start)
- [Usage](#usage)
- [Testing](#testing)
- [Input and output rules](#input-and-output-rules)
- [Project layout](#project-layout)

## Why this package
KickbackCalculator is a minimal Python package for a very specific job: take semicolon-separated CSV input, group rows by currency, customer, and kickback percent, then emit a clean CSV report with per-group kickbacks and per-currency totals.

It is designed as both a reusable library and a command-line tool. That means you can call `calculate_kickbacks(csv_text)` directly in tests or scripts, or run the `kickback-calculator` command against files from your shell.

The implementation stays intentionally small and standard-library only. There is no web framework, no database, no external CSV dependency, and no runtime package beyond Python itself.

## Features
- Library API: `kickbackcalculator.calculate_kickbacks(csv_text: str) -> str`
- CLI command: `kickback-calculator input.csv -o output.csv`
- Stdout fallback when `-o/--output` is omitted
- UTF-8 input and output by default, with `--encoding` support
- Semicolon-delimited CSV parsing via the Python standard library
- Skips the first row as a header
- Ignores blank rows and rows with fewer than 11 columns
- Uses fixed PHP-compatible columns: customer=2, currency=8, amount=9, kickback percent=10
- Uses `decimal.Decimal` internally for money-like calculations
- Emits per-currency `TOTAL` rows
- Formats output with two decimals, decimal comma, and space thousands separators
- Deterministic output ordering

## Requirements
- Python >=3.11 (Python 3.11 and 3.12 supported)
- Standard library only at runtime
- `pytest ^8.0` for development and testing
- No framework required

## Installation
KickbackCalculator is published to PyPI as `jake142-kickbackcalculator`.

### Install from PyPI
```bash
uv pip install jake142-kickbackcalculator
```

### Development
If you cloned the repository, install the project and its dev dependencies with:
```bash
uv sync
```

## Configuration
KickbackCalculator does not use environment variables or config keys.

- Environment variables: none
- Config keys: none

## Quick start
Create a small input file and run the CLI:

```bash
cat > input.csv <<'CSV'
col0;col1;col2;col3;col4;col5;col6;col7;col8;col9;col10
x;y;Customer A;z;z;z;z;z;SEK;1000,00;10
x;y;Customer A;z;z;z;z;z;SEK;500,00;10
CSV

kickback-calculator input.csv -o output.csv
cat output.csv
```

Expected output:

```csv
customer;kickback;currency
Customer A;150,00;SEK
TOTAL;150,00;SEK
```

## Usage

### Python API
Use the public function when you want to convert CSV text in memory:

```python
from kickbackcalculator import calculate_kickbacks

csv_text = """col0;col1;col2;col3;col4;col5;col6;col7;col8;col9;col10
x;y;Customer A;z;z;z;z;z;SEK;1000,00;10
x;y;Customer A;z;z;z;z;z;SEK;500,00;10
"""

result = calculate_kickbacks(csv_text)
print(result)
```

### CLI
Convert a file and write the result to another file:

```bash
kickback-calculator input.csv -o output.csv
```

Write to stdout instead:

```bash
kickback-calculator input.csv
```

Read and write using a different encoding if needed:

```bash
kickback-calculator input.csv -o output.csv --encoding latin-1
```

## Input and output rules
### Input format
- Delimiter: semicolon (`;`)
- The first row is always treated as a header and skipped
- Blank rows are ignored
- Rows with fewer than 11 columns are ignored
- Fixed zero-based columns:
  - customer: column 2
  - currency: column 8
  - amount: column 9
  - kickback percent: column 10

### Parsing rules
- Amount and kickback percent values are trimmed before parsing
- Decimal commas are normalized to decimal points before conversion
- Malformed numeric rows are skipped by default
- The library does not print warnings
- The CLI reports user/input errors concisely on stderr

### Grouping and totals
Rows are grouped by:
1. currency
2. customer
3. kickback percent

For each group, kickback is calculated as:

```text
summed amount * percent / 100
```

The output then appends one `TOTAL` row per currency.

### Output format
- Header: `customer;kickback;currency`
- Rows: `{customer};{formatted_kickback};{currency}`
- Totals: `TOTAL;{formatted_total};{currency}`
- Numbers use exactly two decimals
- Decimal comma is used in output
- A space is used as the thousands separator
- Output ends with a trailing newline

Example formatting:
- `1234.5` -> `1 234,50`
- `10` -> `10,00`

## Testing
Run the test suite with uv:

```bash
uv run pytest
```

The tests cover the public library API and the CLI behavior, including file output and stdout fallback. No external services are called.

## Project layout
The package uses a small `src/` layout:

```text
pyproject.toml
README.md
src/kickbackcalculator/__init__.py
src/kickbackcalculator/core.py
src/kickbackcalculator/cli.py
tests/test_core.py
tests/test_cli.py
```

The public import path is `kickbackcalculator`, and the console script is `kickback-calculator`.
