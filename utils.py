from datetime import datetime

import yaml

from constants import active_fiscal_year

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

print(get_log_id("IND"))