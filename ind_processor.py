from dataclasses import dataclass
from pathlib import Path
from time import sleep
from typing import Optional

import fitz
import yaml
from rich.console import Console
from rich.traceback import install

from constants import Criteria, LimitMatrix
from formatting import Formatter
from utils import get_log_id

install(show_locals=True)

console = Console()


@dataclass
class IndProcessor:
    log_id: str = ""
    employee_name: str = "employee_name"
    monetary_amount: str = ""
    time_off_amount: str = ""
    employee_org: str = "organization"
    employee_pay_plan: str = "pay_plan_gradestep_1"

    sas_monetary_amount: str = "undefined"
    sas_time_off_amount: str = "hours_2"
    ots_monetary_amount: str = "on_the_spot_award"
    ots_time_off_amount: str = "hours"

    nominator_name: str = "please_print"
    nominator_org: str = "org"

    certfier_name: str = "special_act_award_funding_string_2"
    certifier_org: str = "org_2"

    supervisor_name: str = "please_print_2"
    supervisor_org: str = "org_3"

    approver_name: str = "please_print_3"
    approver_org: str = "org_4"

    administrator_name: str = "please_print_4"
    reviewer_name: str = "please_print_5"
    funding_string: str = "special_act_award_funding_string_1"

    justification: str = "extent_of_application"
    value: str = ""
    extent: str = ""
    type: str = ""

    category: str = "IND"

    def items(self) -> dict[str, Optional[str]]:
        """
        Returns a dictionary of the class attributes and their values.
        """

        return dict(self.__dict__)

    def extract_data(self, pdf_path: Path) -> None:
        """
        Extracts the data from the PDF file using PyMuPDF.
        """

        with console.status("[dodger_blue1]Extracting data from PDF...[/dodger_blue1]"):
            sleep(2)

            pdf_data = {}
            with fitz.open(pdf_path) as doc:
                for page in doc:
                    for field in page.widgets():
                        key = Formatter(field.field_name).key()
                        val = Formatter(field.field_value).value()
                        pdf_data[key] = val
            self.data: dict[str, Optional[str]] = pdf_data

            console.print("[spring_green3]> Data extracted from PDF[/spring_green3]")

    def populate_attrs(self) -> None:
        """
        Populates the class attributes with the extracted data.
        """

        if not hasattr(self, "data"):
            raise ValueError("No data extracted from the PDF.")
        if not self.data:
            raise ValueError("No data extracted from the PDF.")

        with console.status("[dodger_blue1]Populating attributes...[/dodger_blue1]"):
            sleep(2)

            if not hasattr(self, "data") or not self.data:
                raise ValueError("No data extracted from the PDF.")
            for field_name, placeholder_value in self.__dict__.items():
                if field_name == "category" or placeholder_value == "":
                    continue
                field_value = self.data.get(placeholder_value)
                self.__setattr__(field_name, field_value)

            console.print(
                "[spring_green3]> Attributes populated from PDF data[/spring_green3]"
            )

    def validate_required_fields(self) -> list[str]:
        """
        Validates that all required fields are populated.
        """

        with console.status(
            "[dodger_blue1]Validating required fields...[/dodger_blue1]"
        ):
            sleep(2)

            required_fields: list[str] = [
                "employee_name",
                "nominator_name",
                "supervisor_name",
                "approver_name",
                "certifier_name",
                "reviewer_name",
                "justification",
            ]
            incomplete_fields: list[str] = [
                field for field in required_fields if getattr(self, field) is None
            ]
            if incomplete_fields:
                incomplete_fields = yaml.safe_dump(incomplete_fields, indent=4)
                raise ValueError(f"Missing Fields:\n{incomplete_fields}")

            console.print(
                "[spring_green3]> All required fields are populated[/spring_green3]"
            )

    def format_fields(self):
        """
        Formats the fields in the class to ensure they are in the correct format.
        """

        with console.status("[dodger_blue1]Formatting fields...[/dodger_blue1]"):
            sleep(2)

            name_fields = [
                "employee_name",
                "nominator_name",
                "certfier_name",
                "supervisor_name",
                "approver_name",
                "administrator_name",
                "reviewer_name",
            ]
            numerical_fields = ["monetary_amount", "time_off_amount"]
            formatted_fields = name_fields + numerical_fields

            for k, v in self.__dict__.items():
                if k not in formatted_fields or v is None:
                    continue
                elif k in name_fields:
                    v = Formatter(v).name()
                elif k in numerical_fields:
                    v = Formatter(v).numerical()
                elif k in ["value", "extent"]:
                    v = v.lower()
                elif k == "reason":
                    v = Formatter(v).reason()
                self.__dict__[k] = v

            console.print(
                "[spring_green3]> Fields formatted successfully[/spring_green3]"
            )

    def classify_amounts(self):
        """
        Classifies the award amounts based on the extracted data.
        """

        with console.status(
            "[dodger_blue1]Classifying award amounts...[/dodger_blue1]"
        ):
            sleep(2)

            sas_fields = [
                "sas_monetary_amount",
                "sas_time_off_amount",
            ]
            sas_values = [
                getattr(self, field) for field in sas_fields if getattr(self, field)
            ]

            if sas_values:
                self.type = "SAS"
                self.monetary_amount = self.sas_monetary_amount
                self.time_off_amount = self.sas_time_off_amount
            else:
                self.type = "OTS"
                self.monetary_amount = self.ots_monetary_amount
                self.time_off_amount = self.ots_time_off_amount

            console.print(
                "[spring_green3]> Award amounts classified successfully[/spring_green3]"
            )

    def get_time_and_monetary_limits(self) -> tuple[int, int]:
        """
        Get the award limits based on value and extent.
        """
        value_index = Criteria.value_options.index(self.value)
        extent_index = Criteria.extent_options.index(self.extent)
        time_off_limit = LimitMatrix.time_off[extent_index][value_index]
        monetary_limit = LimitMatrix.monetary[extent_index][value_index]
        return time_off_limit, monetary_limit

    def validate_amounts(self):
        """
        Validates the monetary and time-off amounts against the limits.
        """

        with console.status("[dodger_blue1]Validating award amounts...[/dodger_blue1]"):
            sleep(2)

            if self.value is None and self.extent is None:
                return

            elif self.monetary_amount == 0 and self.time_off_amount == 0:
                raise ValueError("Both monetary and time off amounts are zero.")

            elif any(
                [
                    self.monetary_amount != int(self.monetary_amount),
                    self.time_off_amount != int(self.time_off_amount),
                ]
            ):
                raise ValueError(
                    "Amounts awarded must be integers.\n"
                    f"Monetary: {self.monetary_amount}\n"
                    f"Time-Off: {self.time_off_amount}"
                )

            elif any(
                [
                    self.value not in Criteria.value_options,
                    self.extent not in Criteria.extent_options,
                ]
            ):
                print(
                    f"Invalid value or extent.\n"
                    f"Value: '{self.value}'\n"
                    f"Extent: '{self.extent}'"
                )
                return

            elif any(
                [
                    self.monetary_amount < 0,
                    self.time_off_amount < 0,
                ]
            ):
                raise ValueError(
                    "Amounts awarded must be positive.\n"
                    f"Monetary: '{self.monetary_amount}'\n"
                    f"Time-Off: '{self.time_off_amount}'"
                )

            time_off_limit, monetary_limit = self.get_time_and_monetary_limits()

            if any(
                [
                    self.monetary_amount > monetary_limit,
                    self.time_off_amount > time_off_limit,
                ]
            ):

                monetary_exceed_percentage = (
                    (self.monetary_amount - monetary_limit) / monetary_limit
                ) * 100

                monetary_exceed_percentage = (
                    f" ({monetary_exceed_percentage}% over limit)"
                    if monetary_exceed_percentage > 0
                    else ""
                )

                time_off_exceed_percentage = (
                    (self.time_off_amount - time_off_limit) / time_off_limit
                ) * 100

                time_off_exceed_percentage = (
                    f" ({time_off_exceed_percentage}% over limit)"
                    if time_off_exceed_percentage > 0
                    else ""
                )

                validation_error_message: str = (
                    "Award amounts exceed the limits for the selected value and extent.\n\n"
                    f"Selections:\n"
                    f"  - Value: {self.value.capitalize()}\n"
                    f"  - Extent: {self.extent.capitalize()}\n\n"
                    f"{self.value.capitalize()} x {self.extent.capitalize()} Limits:\n"
                    f"  - Monetary: ${monetary_limit}\n"
                    f"  - Time-Off: {time_off_limit} hrs\n\n"
                    f"Totals:\n"
                    f"  - Monetary: ${self.monetary_amount}{monetary_exceed_percentage}\n"
                    f"  - Time-Off: {self.time_off_amount} hrs{time_off_exceed_percentage}"
                )
                raise ValueError(validation_error_message)

            console.print(
                "[spring_green3]> Award amounts validated successfully[/spring_green3]"
            )
        self.log_id = get_log_id(self.category)

    def save(self) -> None:
        """
        Saves the processed data to a YAML file.
        """

        with console.status("[dodger_blue1]Saving data to YAML file...[/dodger_blue1]"):
            sleep(2)

            yaml_path = Path("output.yaml")
            if not yaml_path.exists():
                yaml_path.touch()

            with open(yaml_path, "a+") as file:
                yaml.safe_dump(
                    self.items(),
                    file,
                    indent=4,
                    sort_keys=False,
                )

            console.print("[spring_green3]> Data saved to YAML file[/spring_green3]")

    def process(self, pdf_path: Path) -> str:
        """
        Processes the PDF file and extracts the data.
        """

        with console.status("[dodger_blue1]Processing PDF file...[/dodger_blue1]"):
            sleep(2)

            if not pdf_path.exists():
                raise FileNotFoundError(f"File not found: {pdf_path}")
            if pdf_path.suffix != ".pdf":
                raise ValueError(f"Invalid file type: {pdf_path.suffix}. Expected .pdf")

            self.extract_data(pdf_path)
            self.populate_attrs()
            self.validate_required_fields()
            self.format_fields()
            self.classify_amounts()
            self.validate_amounts()
            self.save()
