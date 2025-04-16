from typing import Optional
from uuid import uuid4

import yaml
from constants import (
    PathManager,
    active_fiscal_year,
    division_map,
    mb_map,
    testing_mode,
)
from formatting import Formatter


class LogID:
    def __init__(self, category: str):
        self.category = category

    def _load(self) -> dict[str, int]:
        try:
            if not PathManager.serial_path.exists():
                raise ValueError(f"Log ID file not found: {PathManager.serial_path}")

            with open(PathManager.serial_path, "r") as file:

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
        if testing_mode:
            return str(uuid4())

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
        if testing_mode:
            return

        log_id_data = self._load()
        log_id_data[self.category] += 1

        with open(PathManager.serial_path, "w") as file:
            yaml.safe_dump(log_id_data, file, indent=4, sort_keys=False)


def find_organization(input_org: str) -> tuple[Optional[str], Optional[str]]:
    """
    Finds the organization matching the input string.
    Returns `None` if match not found.
    """
    if not input_org:
        return
    formatted_input = Formatter(input_org).org_div_match()

    org_match: Optional[str] = None
    div_match: Optional[str] = None
    for target_org, div_list in division_map.items():
        formatted_org = Formatter(target_org).org_div_match()
        div_list = list(reversed(div_list))

        if formatted_org in formatted_input:
            org_match = target_org

        for target_div in div_list:
            formatted_div = Formatter(target_div).org_div_match()

            if formatted_div in formatted_input or formatted_input in formatted_div:
                org_match = target_org
                div_match = target_div

        if org_match and div_match:
            break

    return org_match, div_match


def find_mgmt_division(input_org: str) -> str:
    if not input_org:
        return

    formatted_input = Formatter(input_org).org_div_match()

    for org, div_list in mb_map.items():
        formatted_org = Formatter(org).org_div_match()

        if formatted_org in formatted_input:
            return org

        for div in div_list:
            formatted_div = Formatter(div).org_div_match()

            if formatted_div in formatted_input:
                return org
    return None


def update_serial_numbers():
    import warnings
    from time import sleep

    import openpyxl
    from constants import Tracker

    warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

    try:
        wb = openpyxl.load_workbook(Tracker.file_path, data_only=True)
        sheet = wb[Tracker.sheet_name]
        xl_ind_val: int = int(sheet[Tracker.ind_coord].value[-3:])
        xl_grp_val: int = int(sheet[Tracker.grp_coord].value[-3:])

        with open(PathManager.serial_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
            yaml_ind_val = data["IND"]
            yaml_grp_val = data["GRP"]

        yaml_ind_val = xl_ind_val if xl_ind_val > yaml_ind_val else yaml_ind_val
        yaml_grp_val = xl_grp_val if xl_grp_val > yaml_grp_val else yaml_grp_val

        with open(PathManager.serial_path, "w", encoding="utf-8") as file:
            yaml.safe_dump(data, file, indent=4, sort_keys=False, encoding="utf-8")

            print(
                f"\n"
                "Updated serial_numbers.yaml\n"
                f"IND: {yaml_ind_val}\n"
                f"GRP: {yaml_grp_val}\n"
            )

    except Exception as e:
        print(f"Unable to update serial_numbers.yaml. {e}")

    warnings.resetwarnings()
    sleep(3)


class ManualEntry:
    @staticmethod
    def load() -> dict[str, str]:
        with open(PathManager.manual_entry_path, "r") as file:
            try:
                data: dict = yaml.safe_load(file)
                return {k: str(v) for k, v in data.items()}
            except Exception as e:
                print(e)

    @staticmethod
    def reset():
        try:
            keys = ManualEntry.load().keys()
            with open(PathManager.manual_entry_path, "w") as file:
                [file.write(f"{k}:\n") for k in keys]
            print(f"{PathManager.manual_entry_path.name} reset.")
        except Exception as e:
            print(e)


def _clean_JSON_output():
    import json

    with open(PathManager.json_output_path, "r", encoding="utf-8") as jfile:
        data_list: list[dict[str, str]] = json.load(jfile)
        initial_count: int = len(data_list)

    for idx, dict_item in enumerate(data_list):
        if len(dict_item.get("log_id")) == 36:
            data_list[idx] = None

    stripped_list = [i for i in data_list if i]
    final_count: int = len(stripped_list)

    items_removed: int = initial_count - final_count

    with open(PathManager.json_output_path, "w", encoding="utf-8") as jfile:
        json.dump(stripped_list, jfile, indent=4, sort_keys=False)
        print(
            f"initial count: {initial_count}\n"
            f"items removed: {items_removed}\n"
            f"final count: {final_count}"
        )


if __name__ == "__main__":
    _clean_JSON_output()
    ManualEntry.reset()
