from __future__ import annotations

from pathlib import Path

import pytest

from kickbackcalculator.cli import main


@pytest.fixture()
def sample_input_file(tmp_path: Path) -> Path:
    path = tmp_path / "input.csv"
    path.write_text(
        "customer;amount;currency;kickback_percent\n"
        "Alice;1000.00;EUR;10\n"
        "Bob;2500.50;EUR;5\n",
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
    assert rendered.startswith("customer;kickback;currency\n")
    assert "Alice" in rendered
    assert "Bob" in rendered
    assert "TOTAL" in rendered
    assert rendered.count("\n") >= 3


def test_main_writes_to_stdout_when_output_is_omitted(sample_input_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main([str(sample_input_file)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert captured.out.startswith("customer;kickback;currency\n")
    assert "Alice" in captured.out
    assert "TOTAL" in captured.out


def test_main_honors_encoding_option(sample_input_file: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    latin1_input = tmp_path / "latin1.csv"
    latin1_input.write_bytes(
        "customer;amount;currency;kickback_percent\n"
        "Jörg;100.00;EUR;10\n".encode("latin-1")
    )
    output_file = tmp_path / "latin1-output.csv"

    exit_code = main([str(latin1_input), "-o", str(output_file), "--encoding", "latin-1"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""

    rendered = output_file.read_text(encoding="utf-8")
    assert "Jörg" in rendered
    assert rendered.startswith("customer;kickback;currency\n")


def test_main_reports_user_input_errors_concisely(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    missing_input = tmp_path / "missing.csv"

    exit_code = main([str(missing_input)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err.strip() != ""
    assert "No such file" in captured.err or "cannot open" in captured.err or "not found" in captured.err
