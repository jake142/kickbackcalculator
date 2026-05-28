"""Core CSV conversion logic for KickbackCalculator."""

from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from io import StringIO

KickbackGroupKey = tuple[str, str, str]

# Input CSV is semicolon-separated.
# The tests use a header row:
#   customer;amount;currency;kickback_percent
# and then data rows with exactly 4 columns.
_CUSTOMER_COLUMN = 0
_AMOUNT_COLUMN = 1
_CURRENCY_COLUMN = 2
_PERCENT_COLUMN = 3
_MINIMUM_COLUMNS = 4

_HUNDRED = Decimal("100")
_TWO_DECIMAL_PLACES = Decimal("0.01")


class KickbackCalculatorError(ValueError):
    """Raised for unrecoverable KickbackCalculator input errors."""


def calculate_kickbacks(csv_text: str) -> str:
    """Convert semicolon-separated input CSV into grouped kickback output CSV.

    The first input row is always treated as a header and skipped. Blank rows,
    rows with fewer than 4 columns, and rows with malformed amount or percent
    values are skipped silently.

    Returned CSV always uses ``;`` as delimiter, starts with the exact header
    ``customer;kickback;currency``, formats money with two decimals, decimal
    comma, and space thousands separators, and ends with a trailing newline.
    """

    if not isinstance(csv_text, str):
        raise KickbackCalculatorError("csv_text must be a string")

    grouped_amounts: dict[KickbackGroupKey, tuple[Decimal, Decimal]] = {}

    reader = csv.reader(StringIO(csv_text), delimiter=";")

    try:
        # Always skip the first row as a header.
        next(reader, None)

        for row in reader:
            if _is_blank_row(row) or len(row) < _MINIMUM_COLUMNS:
                continue

            try:
                amount = _parse_decimal_value(row[_AMOUNT_COLUMN])
                percent = _parse_decimal_value(row[_PERCENT_COLUMN])
            except (InvalidOperation, ValueError):
                continue

            currency = row[_CURRENCY_COLUMN].strip()
            customer = row[_CUSTOMER_COLUMN].strip()
            percent_key = _decimal_key(percent)
            group_key: KickbackGroupKey = (currency, customer, percent_key)

            if group_key in grouped_amounts:
                existing_amount, existing_percent = grouped_amounts[group_key]
                grouped_amounts[group_key] = (existing_amount + amount, existing_percent)
            else:
                grouped_amounts[group_key] = (amount, percent)
    except csv.Error as exc:
        raise KickbackCalculatorError("could not parse CSV input") from exc

    return _render_output(grouped_amounts)


def _is_blank_row(row: list[str]) -> bool:
    return not row or all(cell.strip() == "" for cell in row)


def _parse_decimal_value(value: str) -> Decimal:
    # Accept common variants:
    # - "1000.00" or "1000,00"
    # - optional non-breaking spaces
    normalized = value.strip().replace("\u00a0", " ").replace(" ", "").replace(",", ".")
    if normalized == "":
        raise ValueError("empty decimal value")

    decimal_value = Decimal(normalized)
    if not decimal_value.is_finite():
        raise ValueError("non-finite decimal value")

    return decimal_value


def _decimal_key(value: Decimal) -> str:
    if value == 0:
        return "0"

    return format(value.normalize(), "f")


def _render_output(grouped_amounts: dict[KickbackGroupKey, tuple[Decimal, Decimal]]) -> str:
    output = StringIO()
    writer = csv.writer(output, delimiter=";", lineterminator="\n")
    writer.writerow(["customer", "kickback", "currency"])

    totals_by_currency: dict[str, Decimal] = {}

    for currency, customer, percent_key in sorted(grouped_amounts):
        amount_sum, percent = grouped_amounts[(currency, customer, percent_key)]
        kickback = amount_sum * percent / _HUNDRED
        totals_by_currency[currency] = totals_by_currency.get(currency, Decimal("0")) + kickback
        writer.writerow([customer, _format_money(kickback), currency])

    for currency, total in totals_by_currency.items():
        writer.writerow(["TOTAL", _format_money(total), currency])

    return output.getvalue()


def _format_money(value: Decimal) -> str:
    rounded = value.quantize(_TWO_DECIMAL_PLACES, rounding=ROUND_HALF_UP)
    # Use space thousands separators and decimal comma.
    return f"{rounded:,.2f}".replace(",", " ").replace(".", ",")


__all__ = ["KickbackCalculatorError", "calculate_kickbacks"]
