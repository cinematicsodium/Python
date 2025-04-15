from typing import Optional

import yaml
from constants import active_fiscal_year, division_map, mb_map, serial_numbers_path
from formatting import Formatter


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


def __update_serial_numbers__():
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

        with open(serial_numbers_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
            yaml_ind_val = data["IND"]
            yaml_grp_val = data["GRP"]

        yaml_ind_val = xl_ind_val if xl_ind_val > yaml_ind_val else yaml_ind_val
        yaml_grp_val = xl_grp_val if xl_grp_val > yaml_grp_val else yaml_grp_val

        with open(serial_numbers_path, "w", encoding="utf-8") as file:
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


__update_serial_numbers__()
