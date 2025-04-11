from datetime import datetime
from pathlib import Path
from typing import Optional

json_output_path: Path
tsv_output_path: Path
serial_numbers_path: Path
logger_path: Path

active_fiscal_year = 2025

today = datetime.today()
if today.month >= 10:
    current_fiscal_year = today.year + 1
else:
    current_fiscal_year = today.year
if current_fiscal_year != active_fiscal_year:
    raise ValueError(
        "Fiscal year mismatch:\n"
        f"Expected: {active_fiscal_year}\n"
        f"Current: {current_fiscal_year}\n"
        "Please update the fiscal year in constants.py."
    )

monetary_matrix: tuple[tuple[int, int, int], ...]
time_off_matrix: tuple[tuple[int, int, int], ...]

division_map: dict[str, list[str]]
mb_map: dict[str, list[str]]
consultant_map: dict[str,str]
