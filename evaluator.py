from typing import Optional

from constants import EvalManager


class AwardEvaluator:
    def __init__(
        self,
        value: str,
        extent: str,
        monetary_amount: int,
        time_off_amount: int,
    ):

        self.value = value
        self.extent = extent
        self.monetary_amount = monetary_amount
        self.time_off_amount = time_off_amount

        self.validate_input()
        self.calculate_limits()
        self.calculate_percentages()

    def validate_input(self) -> Optional[str]:
        """
        Validates the input values and extent.
        """
        error_messages = []
        if self.value not in EvalManager.value_options:
            error_messages.append(f"Invalid 'Value' Selection: '{self.value}'")
        if self.extent not in EvalManager.extent_options:
            error_messages.append(f"Invalid 'Extent' Selection: '{self.extent}'")

        if error_messages:
            error_messages.insert(0, "Assessment validation failed:")
            raise SyntaxError("\n".join(error_messages))

    def calculate_limits(self):
        """
        Calculates the monetary and time-off limits based on value and extent.
        """

        val_idx: Optional[int] = EvalManager.value_options.index(self.value)
        ext_idx: Optional[int] = EvalManager.extent_options.index(self.extent)

        self.monetary_limit: int = EvalManager.monetary_matrix[val_idx][ext_idx]
        self.time_off_limit: int = EvalManager.time_off_matrix[val_idx][ext_idx]

    def calculate_percentages(self):
        """
        Calculates the monetary, time-off, and combined percentages.
        """
        self.monetary_percentage: float = (
            self.monetary_amount / self.monetary_limit
        ) * 100
        self.time_off_percentage: float = (
            self.time_off_amount / self.time_off_limit
        ) * 100
        self.combined_percentage: float = (
            self.monetary_percentage + self.time_off_percentage
        )

    def construct_error_message(self) -> str:
        """
        Constructs an error message if the combined percentage exceeds 100%.
        """
        value: str = str(self.value).capitalize()
        extent: str = str(self.extent).capitalize()
        return (
            "Award amounts exceed the limits for the selected value and extent.\n\n"
            f"Selected Criteria:\n"
            f"  • Value:     {value}\n"
            f"  • Extent:    {extent}\n\n"
            f"Applicable Limits for {value} x {extent}:\n"
            f"  • Monetary:  ${self.monetary_limit}\n"
            f"  • Time-Off:  {self.time_off_limit} hours\n\n"
            f"Award Amounts:\n"
            + f"  • Monetary:  ${self.monetary_amount}".ljust(26)
            + f"({self.monetary_percentage:,.2f}% of ${self.monetary_limit} monetary limit)\n"
            + f"  • Time-Off:  {self.time_off_amount} hours".ljust(26)
            + f"({self.time_off_percentage:,.2f}% of {self.time_off_limit} time-off limit)\n\n"
            + f"Total Percentage:\n"
            + f"  • {self.combined_percentage:,.2f}%:".ljust(15)
            + "Exceeds 100% limit\n\n"
        )

    def evaluate(self) -> None:
        if self.combined_percentage > 100:
            raise ValueError(self.construct_error_message())

        return f"Award evaluation results: {self.combined_percentage:,.2f}%, within limits."
