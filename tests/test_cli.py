from __future__ import annotations

from pathlib import Path

import pytest

from kickbackcalculator.cli import main


@pytest.fixture()
def sample_input_file(tmp_path: Path) -> Path:
    path = tmp_path / "input.csv"
    path.write_text(
        "col0;col1;col2;col3;col4;col5;col6;col7;col8;col9;col10\n"
        "x;y;Customer A;z;z;z;z;z;SEK;1000,00;10\n"
        "x;y;Customer A;z;z;z;z;z;SEK;500,00;10\n",
        encoding="utf-8",
    )
    return path


def test_main_writes_output_file(sample_input_file: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    output_file = tmp_path / "output.csv"

    exit_code = main([str(sample_input_file), "-o", str(output_file)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""

    assert output_file.exists()
    rendered = output_file.read_text(encoding="utf-8")
    assert rendered == (
        "customer;kickback;currency\n"
        "Customer A;150,00;SEK\n"
        "TOTAL;150,00;SEK\n"
    )


def test_main_writes_to_stdout_when_output_is_omitted(sample_input_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main([str(sample_input_file)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert captured.out == (
        "customer;kickback;currency\n"
        "Customer A;150,00;SEK\n"
        "TOTAL;150,00;SEK\n"
    )


def test_main_honors_encoding_option(sample_input_file: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    latin1_input = tmp_path / "latin1.csv"
    latin1_input.write_bytes(
        (
            "col0;col1;col2;col3;col4;col5;col6;col7;col8;col9;col10\n"
            "x;y;J\u00f6rg;z;z;z;z;z;EUR;100,00;10\n"
        ).encode("latin-1")
    )
    output_file = tmp_path / "latin1-output.csv"

    exit_code = main([str(latin1_input), "-o", str(output_file), "--encoding", "latin-1"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""

    rendered = output_file.read_text(encoding="utf-8")
    assert "J\u00f6rg" in rendered
    assert rendered.startswith("customer;kickback;currency\n")


def test_main_reports_user_input_errors_concisely(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    missing_input = tmp_path / "missing.csv"

    exit_code = main([str(missing_input)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err.strip() != ""
    assert "No such file" in captured.err or "cannot open" in captured.err or "not found" in captured.err
