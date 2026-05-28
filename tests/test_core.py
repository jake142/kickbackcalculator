import csv
from io import StringIO

import pytest

from kickbackcalculator import KickbackCalculatorError, calculate_kickbacks


class test_core:
    def test_calculate_kickbacks_single_row(self):
        csv_text = (
            "customer;amount;currency;kickback_percent\n"
            "Alice;100;EUR;10\n"
        )

        result = calculate_kickbacks(csv_text)

        rows = list(csv.reader(StringIO(result), delimiter=";"))
        assert rows == [
            ["customer", "kickback", "currency"],
            ["Alice", "10,00", "EUR"],
            ["TOTAL", "10,00", "EUR"],
        ]

    def test_calculate_kickbacks_groups_rows_and_adds_currency_totals(self):
        csv_text = (
            "customer;amount;currency;kickback_percent\n"
            "Alice;100;EUR;10\n"
            "Alice;50;EUR;10\n"
            "Bob;200;USD;5\n"
        )

        result = calculate_kickbacks(csv_text)

        rows = list(csv.reader(StringIO(result), delimiter=";"))
        assert rows == [
            ["customer", "kickback", "currency"],
            ["Alice", "15,00", "EUR"],
            ["TOTAL", "15,00", "EUR"],
            ["Bob", "10,00", "USD"],
            ["TOTAL", "10,00", "USD"],
        ]

    def test_calculate_kickbacks_parses_decimal_commas_and_formats_thousands_with_spaces(self):
        csv_text = (
            "customer;amount;currency;kickback_percent\n"
            "Alice;1234,56;EUR;12,5\n"
        )

        result = calculate_kickbacks(csv_text)

        rows = list(csv.reader(StringIO(result), delimiter=";"))
        assert rows[1] == ["Alice", "154,32", "EUR"]
        assert rows[2] == ["TOTAL", "154,32", "EUR"]

    def test_calculate_kickbacks_skips_blank_short_and_malformed_rows(self):
        csv_text = (
            "customer;amount;currency;kickback_percent\n"
            "\n"
            "Too;Short\n"
            "Alice;100;EUR;10\n"
            "Bob;not-a-number;EUR;10\n"
            "Carol;200;EUR;5\n"
        )

        result = calculate_kickbacks(csv_text)

        rows = list(csv.reader(StringIO(result), delimiter=";"))
        assert rows == [
            ["customer", "kickback", "currency"],
            ["Alice", "10,00", "EUR"],
            ["Carol", "10,00", "EUR"],
            ["TOTAL", "20,00", "EUR"],
        ]

    def test_calculate_kickbacks_rejects_empty_or_header_only_input(self):
        with pytest.raises(KickbackCalculatorError):
            calculate_kickbacks("")

        with pytest.raises(KickbackCalculatorError):
            calculate_kickbacks("customer;amount;currency;kickback_percent\n")
