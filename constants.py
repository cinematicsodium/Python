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


class Criteria:
    """
    Award evaluation criteria.
    """

    value_options: tuple[str, ...] = ("a", "b", "c")
    extent_options: tuple[str, ...] = ("limited", "general", "exceptional")


class LimitMatrix:
    time_off: tuple[tuple[int, ...], ...] = ((1, 2, 3), (4, 5, 6), (7, 8, 9))
    monetary: tuple[tuple[int, ...], ...] = (
        (10, 20, 30),
        (40, 50, 60),
        (70, 80, 90),
    )
