import csv
from io import StringIO

import pytest

from kickbackcalculator import KickbackCalculatorError, calculate_kickbacks


class TestCore:
    def test_calculate_kickbacks_single_row(self):
        csv_text = (
            "h0;h1;h2;h3;h4;h5;h6;h7;h8;h9;h10\n"
            "a;b;Alice;d;e;f;g;h;EUR;100;10\n"
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
            "h0;h1;h2;h3;h4;h5;h6;h7;h8;h9;h10\n"
            "a;b;Alice;d;e;f;g;h;EUR;100;10\n"
            "a;b;Alice;d;e;f;g;h;EUR;50;10\n"
            "a;b;Bob;d;e;f;g;h;USD;200;5\n"
        )

        result = calculate_kickbacks(csv_text)

        rows = list(csv.reader(StringIO(result), delimiter=";"))
        assert rows == [
            ["customer", "kickback", "currency"],
            ["Alice", "15,00", "EUR"],
            ["Bob", "10,00", "USD"],
            ["TOTAL", "15,00", "EUR"],
            ["TOTAL", "10,00", "USD"],
        ]

    def test_calculate_kickbacks_parses_decimal_commas_and_formats_thousands_with_spaces(self):
        csv_text = (
            "h0;h1;h2;h3;h4;h5;h6;h7;h8;h9;h10\n"
            "a;b;Alice;d;e;f;g;h;EUR;12345,00;10\n"
        )

        result = calculate_kickbacks(csv_text)

        rows = list(csv.reader(StringIO(result), delimiter=";"))
        assert rows[1] == ["Alice", "1 234,50", "EUR"]
        assert rows[2] == ["TOTAL", "1 234,50", "EUR"]

    def test_calculate_kickbacks_skips_blank_short_and_malformed_rows(self):
        csv_text = (
            "h0;h1;h2;h3;h4;h5;h6;h7;h8;h9;h10\n"
            "\n"
            "Too;Short\n"
            "a;b;Alice;d;e;f;g;h;EUR;100;10\n"
            "a;b;Bob;d;e;f;g;h;EUR;not-a-number;10\n"
            "a;b;Carol;d;e;f;g;h;EUR;200;bad-percent\n"
            "a;b;Dave;d;e;f;g;h;EUR;200;5\n"
        )

        result = calculate_kickbacks(csv_text)

        rows = list(csv.reader(StringIO(result), delimiter=";"))
        assert rows == [
            ["customer", "kickback", "currency"],
            ["Alice", "10,00", "EUR"],
            ["Dave", "10,00", "EUR"],
            ["TOTAL", "20,00", "EUR"],
        ]

    def test_calculate_kickbacks_skips_header_row_even_if_it_looks_like_data(self):
        csv_text = (
            "a;b;Header Customer;d;e;f;g;h;SEK;1000,00;10\n"
            "a;b;Alice;d;e;f;g;h;SEK;500,00;10\n"
        )

        result = calculate_kickbacks(csv_text)

        rows = list(csv.reader(StringIO(result), delimiter=";"))
        assert rows == [
            ["customer", "kickback", "currency"],
            ["Alice", "50,00", "SEK"],
            ["TOTAL", "50,00", "SEK"],
        ]

    def test_calculate_kickbacks_groups_percent_values_like_php_float_strings(self):
        csv_text = (
            "h0;h1;h2;h3;h4;h5;h6;h7;h8;h9;h10\n"
            "a;b;Alice;d;e;f;g;h;EUR;100;10\n"
            "a;b;Alice;d;e;f;g;h;EUR;50;10,0\n"
            "a;b;Alice;d;e;f;g;h;EUR;25;10.0\n"
        )

        result = calculate_kickbacks(csv_text)

        rows = list(csv.reader(StringIO(result), delimiter=";"))
        assert rows == [
            ["customer", "kickback", "currency"],
            ["Alice", "17,50", "EUR"],
            ["TOTAL", "17,50", "EUR"],
        ]

    def test_calculate_kickbacks_sorts_by_combined_php_style_key(self):
        csv_text = (
            "h0;h1;h2;h3;h4;h5;h6;h7;h8;h9;h10\n"
            "a;b;Zed;d;e;f;g;h;USD;100;10\n"
            "a;b;Anna;d;e;f;g;h;EUR;100;10\n"
            "a;b;Bob;d;e;f;g;h;EUR;100;5\n"
        )

        result = calculate_kickbacks(csv_text)

        rows = list(csv.reader(StringIO(result), delimiter=";"))
        assert rows == [
            ["customer", "kickback", "currency"],
            ["Anna", "10,00", "EUR"],
            ["Bob", "5,00", "EUR"],
            ["Zed", "10,00", "USD"],
            ["TOTAL", "15,00", "EUR"],
            ["TOTAL", "10,00", "USD"],
        ]

    def test_calculate_kickbacks_returns_trailing_newline(self):
        csv_text = (
            "h0;h1;h2;h3;h4;h5;h6;h7;h8;h9;h10\n"
            "a;b;Alice;d;e;f;g;h;EUR;100;10\n"
        )

        result = calculate_kickbacks(csv_text)

        assert result.endswith("\n")

    def test_calculate_kickbacks_rejects_non_string_input(self):
        with pytest.raises(KickbackCalculatorError):
            calculate_kickbacks(None)  # type: ignore[arg-type]
