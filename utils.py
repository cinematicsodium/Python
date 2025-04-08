from typing import Optional

import yaml

from constants import active_fiscal_year, division_map, mb_map
from formatting import Formatter

_log_id_yaml = "log_id.yaml"


def get_log_id(category: str) -> int:
    """
    Retrieves the log ID from the JSON file formatted as {fiscal_year}-{category}-{serial_number}.
    Increments the serial number for the next use.
    """
    with open(_log_id_yaml, "r+") as file:
        log_id_data = yaml.safe_load(file)

        if not log_id_data:
            raise ValueError("Log ID data not found in JSON file.")
        elif not isinstance(log_id_data, dict):
            raise ValueError("Log ID data is not in the expected dictionary format.")
        elif category not in log_id_data:
            raise ValueError(f"Log ID data does not contain '{category}' key.")
        elif not isinstance(log_id_data.get(category), int):
            raise ValueError(
                f"Log ID data for '{category}' is not in the expected integer format."
            )

        fy_str = str(active_fiscal_year)[-2:]
        log_serial = str(log_id_data[category]).zfill(3)
        log_id = f"{fy_str}-{category}-{log_serial}"

        log_id_data[category] += 1

        file.seek(0)
        yaml.safe_dump(log_id_data, file, indent=4, sort_keys=False)
        file.truncate()

    return log_id

def find_organization(input_org: str, get_div: bool = False) -> Optional[str]:
    """
    Finds the organization matching the input string.
    """
    formatted_input = Formatter(input_org).org_div()

    for org, div_list in division_map.items():
        formatted_org = Formatter(org).org_div()
    
        if formatted_org in formatted_input and not get_div:
            return org

        for div in div_list:
            formatted_div = Formatter(div).org_div()
    
            if formatted_div in formatted_input:
                return div if get_div else org
    return None

def find_mgmt_division(input_org: str) -> str:
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
