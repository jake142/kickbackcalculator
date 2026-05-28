"""Core CSV conversion logic for KickbackCalculator."""

from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from io import StringIO

KickbackGroupKey = tuple[str, str, str]

# PHP-compatible semicolon CSV input contract.
_CUSTOMER_COLUMN = 2
_CURRENCY_COLUMN = 8
_AMOUNT_COLUMN = 9
_PERCENT_COLUMN = 10
_MINIMUM_COLUMNS = 11

_HUNDRED = Decimal("100")
_TWO_DECIMAL_PLACES = Decimal("0.01")


class KickbackCalculatorError(ValueError):
    """Raised for unrecoverable KickbackCalculator input errors."""


def calculate_kickbacks(csv_text: str) -> str:
    """Convert semicolon-separated input CSV into grouped kickback output CSV.

    The first input row is always treated as a header and skipped. Blank rows,
    rows with fewer than 11 columns, and rows with malformed amount or percent
    values are skipped silently.

    Returned CSV always uses ``;`` as delimiter, starts with the exact header
    ``customer;kickback;currency``, formats money with two decimals, decimal
    comma, and space thousands separators, and ends with a trailing newline.
    """

    if not isinstance(csv_text, str):
        raise KickbackCalculatorError("csv_text must be a string")

    grouped_amounts: dict[KickbackGroupKey, Decimal] = {}

    reader = csv.reader(StringIO(csv_text), delimiter=";")

    try:
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
            grouped_amounts[group_key] = grouped_amounts.get(group_key, Decimal("0")) + amount
    except csv.Error as exc:
        raise KickbackCalculatorError("could not parse CSV input") from exc

    return _render_output(grouped_amounts)


def _is_blank_row(row: list[str]) -> bool:
    return not row or all(cell.strip() == "" for cell in row)


def _parse_decimal_value(value: str) -> Decimal:
    normalized = value.strip().replace("\u00a0", " ").replace(" ", "").replace(",", ".")
    if normalized == "":
        raise ValueError("empty decimal value")

    decimal_value = Decimal(normalized)
    if not decimal_value.is_finite():
        raise ValueError("non-finite decimal value")

    return decimal_value


def _decimal_key(value: Decimal) -> str:
    """Normalize percent so values like 10, 10,0, and 10.0 group together."""

    if value == 0:
        return "0"
    # PHP float->string behavior is close to removing trailing zeros.
    return format(value.normalize(), "f")


def _php_combined_key(currency: str, customer: str, percent_key: str) -> str:
    # PHP contract: currency + '_' + customer + '_' + kickbackPercent
    return f"{currency}_{customer}_{percent_key}"


def _render_output(grouped_amounts: dict[KickbackGroupKey, Decimal]) -> str:
    output = StringIO()
    writer = csv.writer(output, delimiter=";", lineterminator="\n")
    writer.writerow(["customer", "kickback", "currency"])

    # Totals must be appended after grouped rows.
    totals_by_currency: dict[str, Decimal] = {}
    currency_order: list[str] = []

    # Sort order must mimic PHP ksort($calculationsArray) on the combined key.
    # The PHP contract sorts by: currency + '_' + customer + '_' + kickbackPercent.
    sorted_items = sorted(
        grouped_amounts.items(),
        key=lambda item: _php_combined_key(item[0][0], item[0][1], item[0][2]),
    )

    for (currency, customer, percent_key), amount_sum in sorted_items:
        percent = Decimal(percent_key)
        kickback = amount_sum * percent / _HUNDRED

        if currency not in totals_by_currency:
            totals_by_currency[currency] = Decimal("0")
            currency_order.append(currency)

        totals_by_currency[currency] = totals_by_currency[currency] + kickback
        writer.writerow([customer, _format_money(kickback), currency])

    for currency in currency_order:
        writer.writerow(["TOTAL", _format_money(totals_by_currency[currency]), currency])

    return output.getvalue()


def _format_money(value: Decimal) -> str:
    rounded = value.quantize(_TWO_DECIMAL_PLACES, rounding=ROUND_HALF_UP)
    return f"{rounded:,.2f}".replace(",", " ").replace(".", ",")


__all__ = ["KickbackCalculatorError", "calculate_kickbacks"]
