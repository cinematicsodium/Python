from datetime import datetime
from pathlib import Path

status: str = "DISABLED"

testing_mode: bool = True
if testing_mode:
    status = "ENABLED"

input(f'\n\nTesting mode {status}.\nPress "Enter" to continue.\n\n').strip()


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


class PathManager:
    archive_path: Path
    json_output_path: Path
    logger_path: Path
    manual_entry_path: Path
    serial_path: Path
    tracker_path: Path
    tsv_output_path: Path

    def __init__(self):
        paths_list: list[Path] = [
            self.json_output_path,
            self.logger_path,
            self.serial_path,
            self.tsv_output_path,
            self.archive_path,
        ]
        for path in paths_list:
            if not path.exists():
                path.touch(exist_ok=True)


class EvalManager:
    value_options: tuple[str, ...]
    extent_options: tuple[str, ...]
    monetary_matrix: tuple[tuple[int, int, int], ...]
    time_off_matrix: tuple[tuple[int, int, int], ...]


class Tracker:
    file_path: Path = PathManager.tracker_path
    sheet_name: str
    ind_coord: str
    grp_coord: str


division_map: dict[str, list[str]]
mb_map: dict[str, list[str]]
consultant_map: dict[str, str]
