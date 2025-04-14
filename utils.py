from typing import Optional

import openpyxl
import yaml
from constants import (
    Tracker,
    active_fiscal_year,
    division_map,
    mb_map,
    serial_numbers_path,
)
from formatting import Formatter
from rich.console import Console

console = Console()


class LogID:
    def __init__(self, category: str):
        self.category = category

    def _load(self) -> dict[str, int]:
        try:
            if not serial_numbers_path.exists():
                raise ValueError(f"Log ID file not found: {serial_numbers_path}")

            with open(serial_numbers_path, "r") as file:

                log_id_data = yaml.safe_load(file)

                if not log_id_data:
                    raise ValueError("Log ID data not found in YAML file.")
                elif not isinstance(log_id_data, dict):
                    raise ValueError(
                        "Log ID data is not in the expected dictionary format."
                    )

            return log_id_data

        except Exception as e:
            raise ValueError(f"Unable to load Log ID data. {e}")

    def get(self) -> int:
        """
        Retrieves the log ID from the JSON file formatted as {fiscal_year}-{category}-{serial_number}.
        """

        log_id_data: dict[str, int] = self._load()
        if self.category not in log_id_data:
            raise ValueError(f"Log ID data does not contain '{self.category}' key.")
        elif not isinstance(log_id_data.get(self.category), int):
            raise ValueError(
                f"Log ID data for '{self.category}' is not in the expected integer format."
            )

        fy_str = str(active_fiscal_year)[-2:]
        log_serial = str(log_id_data[self.category]).zfill(3)
        log_id = f"{fy_str}-{self.category}-{log_serial}"
        return log_id

    def save(self) -> None:
        log_id_data = self._load()
        log_id_data[self.category] += 1

        with open(serial_numbers_path, "w") as file:
            yaml.safe_dump(log_id_data, file, indent=4, sort_keys=False)


def find_organization(input_org: str, get_div: bool = False) -> Optional[str]:
    """
    Finds the organization matching the input string.
    Returns `None` if match not found.
    """
    if not input_org:
        return
    formatted_input = Formatter(input_org).org_div()

    org_div_match: Optional[str] = None
    for org, div_list in division_map.items():
        formatted_org = Formatter(org).org_div()

        if formatted_org in formatted_input:
            org_div_match = org
            if not get_div:
                break

        for div in div_list:
            formatted_div = Formatter(div).org_div()

            if formatted_div in formatted_input:
                org_div_match = div if get_div else org
                break
    return org_div_match


def find_mgmt_division(input_org: str) -> str:
    if not input_org:
        return

    formatted_input = Formatter(input_org).org_div()

    for org, div_list in mb_map.items():
        formatted_org = Formatter(org).org_div()

        if formatted_org in formatted_input:
            return org

        for div in div_list:
            formatted_div = Formatter(div).org_div()

            if formatted_div in formatted_input:
                return org
    return None


def _get_serial_numbers_from_tracker() -> Optional[tuple[int, int]]:
    try:
        wb = openpyxl.load_workbook(Tracker.file_path, data_only=True)
        sheet = wb[Tracker.sheet_name]
        ind_val: int = int(sheet[Tracker.ind_coord].value[-3:])
        grp_val: int = int(sheet[Tracker.grp_coord].value[-3:])
        return ind_val, grp_val
    except:
        return None


def _update_serial_numbers() -> None:
    if (tracker_serial_numbers := _get_serial_numbers_from_tracker()) is None:
        return
    ind_val, grp_val = tracker_serial_numbers
    try:
        with open(serial_numbers_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
        data["IND"] = ind_val if ind_val > data["IND"] else data["IND"]
        data["GRP"] = grp_val
        with open(serial_numbers_path, "w", encoding="utf-8") as file:
            yaml.safe_dump(data, file, indent=4, sort_keys=False, encoding="utf-8")
    except Exception as e:
        from time import sleep

        print(f"Unable to update serial_numbers.yaml. {e}")
        sleep(3)


_update_serial_numbers()
