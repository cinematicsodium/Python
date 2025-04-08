from datetime import datetime

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


class Assessment:
    """
    Award evaluation criteria.
    """

    value_options: tuple[str, ...] = ("moderate", "high", "exceptional")
    extent_options: tuple[str, ...] = ("limited", "general", "extended")


class LimitsMatrix:
    monetary: tuple[tuple[int, ...], ...] = (
        (500, 1000, 3000),  # moderate
        (1000, 3000, 6000),  # high
        (3000, 6000, 10000),  # exceptional
        # limited   extended    general
    )
    time_off: tuple[tuple[int, ...], ...] = (
        (9, 18, 27),  # moderate
        (18, 27, 36),  # high
        (27, 36, 40),  # exceptional
        # limited   extended    general
    )


division_map: dict[str, list[str]] = {}
