from typing import Optional
from constants import monetary_matrix, time_off_matrix


class AwardEvaluator:
    """
    Class for evaluating award criteria.
    * value: str - The value of the award (moderate, high, exceptional).
    * extent: str - The extent of the award (limited, extended, general).
    """
    value_options: tuple[str, ...] = ("moderate", "high", "exceptional")
    extent_options: tuple[str, ...] = ("limited", "extended", "general")
    def __init__(self,value: str, extent: str, monetary_amount: int, time_off_amount: int,):

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
        if self.value not in self.value_options:
            error_messages.append(f"Invalid 'Value' Selection: '{self.value}'")
        if self.extent not in self.extent_options:
            error_messages.append(f"Invalid 'Extent' Selection: '{self.extent}'")

        if error_messages:
            error_messages.insert(0,"Assessment validation failed:")
            raise ValueError("\n".join(error_messages))

    def calculate_limits(self):
        """
        Calculates the monetary and time-off limits based on value and extent.
        """

        val_idx: Optional[int] = self.value_options.index(self.value)
        ext_idx: Optional[int] = self.extent_options.index(self.extent)

        self.monetary_limit: int = monetary_matrix[val_idx][ext_idx]
        self.time_off_limit: int = time_off_matrix[val_idx][ext_idx]

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
        return (
            "Award amounts exceed the limits for the selected value and extent.\n\n"
            f"Selected Criteria:\n"
            f"  • Value:     {self.value.capitalize()}\n"
            f"  • Extent:    {self.extent.capitalize()}\n\n"
            f"Applicable Limits for {self.value.capitalize()} x {self.extent.capitalize()}:\n"
            f"  • Monetary:  ${self.monetary_limit}\n"
            f"  • Time-Off:  {self.time_off_limit} hrs\n\n"
            f"Award Amounts:\n"
            + f"  • Monetary:  ${self.monetary_amount}".ljust(26)
            + f"({self.monetary_percentage:,.2f}% of ${self.monetary_limit} monetary limit)\n"
            + f"  • Time-Off:  {self.time_off_amount} hrs".ljust(26)
            + f"({self.time_off_percentage:,.2f}% of {self.time_off_limit} time-off limit)\n\n"
            + f"Total Percentage:\n"
            + f"  • {self.combined_percentage:,.2f}%".ljust(15)
            +"Exceeds 100% limit"
        )

    def evaluate(self) -> None:
        error_message = self.validate_input()
        if error_message is not None:
            return f"[red]Validation Error:[/red]\n{error_message}[/red]"

        if self.combined_percentage > 100:
            error_message = self.construct_error_message()
            raise ValueError(error_message)

        return f"[spring_green3]> Award evaluation results: {self.combined_percentage:,.2f}%, within limits.[/spring_green3]"
