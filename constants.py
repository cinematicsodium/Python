from datetime import datetime
from pathlib import Path
from typing import Optional

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

_local_dir: Path
_network_dir: Path

json_output_path: Path = _local_dir / Path()
tsv_output_path: Path = _local_dir / Path()
serial_numbers_path: Path = _local_dir / Path()
logger_path: Path = _local_dir / Path()
archive_path: Path = _network_dir / Path()
archive_path.mkdir(parents=True, exist_ok=True)


class Tracker:
    file_path: Path = _local_dir / Path()
    sheet_name: str = "data_entry"
    ind_coord: str = "C2"
    grp_coord: str = "C3"


monetary_matrix: tuple[tuple[int, int, int], ...] = (
    (0, 0, 0),
    (0, 0, 0),
    (0, 0, 0),
)
time_off_matrix: tuple[tuple[int, int, int], ...] = (
    (0, 0, 0),
    (0, 0, 0),
    (0, 0, 0),
)


division_map: dict[str, list[str]]
mb_map: dict[str, list[str]]
consultant_map: dict[str, str]
