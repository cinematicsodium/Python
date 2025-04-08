import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import sleep
from typing import Optional

import fitz
import yaml
from rich import print as pprint
from rich.console import Console
from rich.traceback import install

from constants import Assessment, LimitsMatrix
from formatting import Formatter
from utils import find_mgmt_division, find_organization, get_log_id

install(show_locals=True)

console = Console()


@dataclass
class IndProcessor:
    log_id: str = ""
    funding_org: str = ""
    employee_name: str = "employee_name"
    monetary_amount: str = ""
    time_off_amount: str = ""
    employee_org: str = "organization"
    employee_pay_plan: str = "pay_plan_gradestep_1"

    nominator_name: str = "please_print"
    nominator_org: str = "org"

    sas_monetary_amount: str = "undefined"
    sas_time_off_amount: str = "hours_2"
    ots_monetary_amount: str = "on_the_spot_award"
    ots_time_off_amount: str = "hours"

    certifier_name: str = "special_act_award_funding_string_2"
    certifier_org: str = "org_2"

    employee_supervisor_name: str = "please_print_2"
    supervisor_org: str = "org_3"

    approver_name: str = "please_print_3"
    approver_org: str = "org_4"

    administrator_name: str = "please_print_4"
    reviewer_name: str = "please_print_5"
    funding_string: str = "special_act_award_funding_string_1"
    mb_division: str = ""

    justification: str = "extent_of_application"
    value: str = ""
    extent: str = ""
    type: str = ""

    category: str = "IND"
    date_received: str = datetime.now().strftime("%Y-%m-%d")

    def output(self) -> dict[str, str]:
        """
        Returns a dictionary of the class attributes and their values.
        """
        _dict_items: dict[str, str] = {}
        for k, v in self.__dict__.items():
            if k == "data":
                continue
            if any(k.startswith(i) for i in ("sas", "ots")):
                continue
            elif k == "justification":
                v = f"{len(v.split(' '))} words"
            else:
                k = k.replace("_", " ").title()
                v = "-" if v is None else v
            _dict_items[k] = v
        console.print(
            "[spring_green3]> Created dictionary for YAML output[/spring_green3]"
        )
        return _dict_items

    def extract_data(self, pdf_path: Path) -> None:
        """
        Extracts the data from the PDF file using PyMuPDF.
        """
        with console.status("[bright_cyan]Extracting data from PDF...[/bright_cyan]"):
            # sleep(1)

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
        with console.status("[bright_cyan]Populating attributes...[/bright_cyan]"):
            # sleep(1)

            exempt_fields: list[str] = [
                "category",
                "data",
                "date_received",
            ]
            if not hasattr(self, "data") or not self.data:
                raise ValueError("No data extracted from the PDF.")
            for field_name, placeholder_value in self.__dict__.items():
                if field_name in exempt_fields or placeholder_value == "":
                    continue
                field_value = self.data.get(placeholder_value)
                self.__setattr__(field_name, field_value)

            value_options: list[str] = [
                k
                for k, v in self.data.items()
                if k in Assessment.value_options and str(v).lower() == "on"
            ]
            self.value = value_options[0] if len(value_options) == 1 else self.value

            console.print("[spring_green3]> Populated attributes[/spring_green3]")

    def find_incomplete_fields(self) -> list[str]:
        """
        Validates that all required fields are populated.
        """
        with console.status("[bright_cyan]Validating required fields...[/bright_cyan]"):
            # sleep(1)

            required_fields: list[str] = [
                "employee_name",
                "nominator_name",
                "employee_supervisor_name",
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

            if "es" in self.employee_pay_plan.lower():
                raise ValueError(
                    f"'ES' pay plans not allowed: {self.employee_pay_plan}"
                )

            console.print(
                "[spring_green3]> All required fields are populated[/spring_green3]"
            )

    def match_org_and_div(self):
        """
        Matches the funding organization based on the values of its organization fields.
        """
        with console.status("[bright_cyan]Matching organization...[/bright_cyan]"):
            # sleep(1)

            org_fields = [
                "employee_org",
                "nominator_org",
                "certifier_org",
                "supervisor_org",
                "approver_org",
            ]

            for org in org_fields:
                try:
                    if search_val := getattr(self, org):
                        if (
                            org_match := find_organization(search_val, get_div=True)
                        ) is not None:
                            setattr(self, org, org_match)
                except:
                    pass

            self.nominator_org = find_organization(self.nominator_org)

            self.funding_org = self.nominator_org

            console.print(
                f"[spring_green3]> Funding org set to '{self.funding_org}'[/spring_green3]"
            )

            if "mb" in self.funding_org.lower():
                try:
                    mb_list = [
                        find_mgmt_division(getattr(self, org))
                        for org in org_fields
                        if hasattr(self, org) and getattr(self, org) is not None
                    ]
                    mb_list = [i for i in mb_list if i is not None]
                    self.mb_division = (
                        Counter(mb_list).most_common(1)[0][0] if mb_list else None
                    )
                    if self.mb_division is not None:
                        console.print(
                            f"[spring_green3]> MB division set to '{self.mb_division}'[/spring_green3]"
                        )
                except:
                    pass

    def format_fields(self) -> None:
        """
        "Prepares object fields for further processing by applying formatting rules."
        """
        with console.status("[bright_cyan]Formatting fields...[/bright_cyan]"):
            # sleep(1)

            name_fields = [
                "employee_name",
                "nominator_name",
                "certfier_name",
                "supervisor_name",
                "approver_name",
                "administrator_name",
                "reviewer_name",
            ]
            numerical_fields = [
                "sas_monetary_amount",
                "sas_time_off_amount",
                "ots_monetary_amount",
                "ots_time_off_amount",
            ]
            justification_field = ["justification"]

            for k, v in self.__dict__.items():
                if v is None:
                    continue
                elif k in name_fields:
                    v = Formatter(v).name()
                elif k in numerical_fields:
                    v = Formatter(v).numerical()
                elif k in justification_field:
                    v = Formatter(v).reason()
                else:
                    continue
                self.__dict__[k] = v

            if isinstance(self.employee_pay_plan, str):
                self.employee_pay_plan = Formatter(self.employee_pay_plan).pay_plan()

            console.print(
                "[spring_green3]> All fields have been formatted[/spring_green3]"
            )

    def categorize_amounts(self):
        """
        Categorizes award amounts as either SAS or OTS based on specific fields.
        """

        with console.status("[bright_cyan]Categorizing award...[/bright_cyan]"):
            # sleep(1)

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

            self.monetary_amount = self.monetary_amount if self.monetary_amount else 0
            self.time_off_amount = self.time_off_amount if self.time_off_amount else 0

            console.print(
                "[spring_green3]> Award type and amount have been determined[/spring_green3]"
            )

    def validate_amounts(self):
        """
        Confirms the award amounts meet the required criteria.
        """

        with console.status(
            "[bright_cyan]Checking award amounts for errors...[/bright_cyan]"
        ):
            # sleep(1)

            if self.monetary_amount == 0 and self.time_off_amount == 0:
                raise ValueError("No monetary or time-off amounts found.")

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
            self.monetary_amount = int(self.monetary_amount)
            self.time_off_amount = int(self.time_off_amount)

            if any(
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

            console.print(
                "[spring_green3]> Award validation stage 1 of 2 complete[/spring_green3]"
            )

    def enforce_limits(self):
        """
        Enforces the monetary and time-off award limits determined by the selected value and extent.
        """

        with console.status("[bright_cyan]Enforcing award limits...[/bright_cyan]"):
            # sleep(1)

            error_message: str = ""
            self.value = self.value if self.value else None
            self.extent = self.extent if self.extent else None
            if self.value not in Assessment.value_options:
                error_message += f"> Invalid Value Selection: {self.value}"
            if self.extent not in Assessment.extent_options:
                error_message += f"> Invalid Extent Selection: {self.extent}"
            if error_message != "":
                console.print(
                    f"[bright_red]> Award validation stage 1 of 2 failed\n{error_message}[/bright_red]"
                )
                return

            value_index = Assessment.value_options.index(self.value)
            extent_index = Assessment.extent_options.index(self.extent)

            time_off_limit = LimitsMatrix.time_off[extent_index][value_index]
            monetary_limit = LimitsMatrix.monetary[extent_index][value_index]

            monetary_percentage: float = (self.monetary_amount / monetary_limit) * 100
            time_off_percentage: float = (self.time_off_amount / time_off_limit) * 100
            combined_percentage: float = monetary_percentage + time_off_percentage

            if monetary_percentage + time_off_percentage > 100:
                combined_percentage: str = (
                    f"{(monetary_percentage+time_off_percentage):.2g}"
                )
                validation_error_message: str = (
                    "Award amounts exceed the limits for the selected value and extent.\n\n"
                    f"Assessment Details:\n"
                    f"  - Value:        {self.value}\n"
                    f"  - Extent:       {self.extent}\n\n"
                    f"{self.value} x {self.extent} Limits:\n"
                    f"  - Monetary:     ${monetary_limit}\n"
                    f"  - Time-Off:     {time_off_limit} hrs\n\n"
                    f"Award Amounts:\n"
                    + f"  - Monetary:   ${self.monetary_amount}".ljust(26)
                    + f"({monetary_percentage:.2g}% of monetary limit)\n"
                    + f"  - Time-Off:   {self.time_off_amount} hrs".ljust(26)
                    + f"({time_off_percentage:.2g}% of time-off limit)\n"
                    + "                 --".ljust(26)
                    + f"({combined_percentage}% of 100% limit)"
                )
                raise ValueError(validation_error_message)

            console.print(
                "[spring_green3]> Award validation stage 2 of 2 complete[/spring_green3]"
            )

    def save_yaml(self) -> None:
        """
        Saves the processed data to a file in YAML format.
        """
        self.log_id = get_log_id(self.category)
        self.date_received = datetime.now().strftime("%Y-%m-%d")

        with console.status("[bright_cyan]Exporting data to YAML...[/bright_cyan]"):
            # sleep(1)

            # yaml_path = Path("output_yaml.yaml")
            output_path = Path("output_json.json")
            if not output_path.exists():
                output_path.touch()
                output_path.write_text("")

            with open(output_path, "r+", encoding="utf-8") as file:
                data: dict[datetime : dict[str, str | int]] = json.load(file)
                if not data:
                    data = {}
                now = datetime.now().replace(microsecond=0)
                # data.update({datetime.now().replace(microsecond=0): self.output()})
                data.update({str(now): self.output()})

                file.seek(0)
                json.dump(data, file, indent=4, sort_keys=False)
                file.truncate()

            console.print("[spring_green3]> Data stored in YAML[/spring_green3]")

    def save_tsv(self) -> None:
        """
        Saves the current data to a TSV file.
        """
        with console.status("[bright_cyan]Saving data to TSV file...[/bright_cyan]"):
            tsv_items: list[str] = [
                self.log_id,
                self.date_received,
                None,
                self.category,
                self.type,
                self.employee_name,
                self.monetary_amount,
                self.time_off_amount,
                self.employee_pay_plan,
                self.employee_org,
                self.employee_supervisor_name,
                None,
                self.nominator_name,
                self.funding_org,
                self.mb_division,
                self.justification,
                self.value,
                self.extent,
            ]
            for idx, item in enumerate(tsv_items):
                if not item:
                    tsv_items[idx] = "-"
                else:
                    tsv_items[idx] = str(item)

            tsv_string = "\t".join(tsv_items)

            tsv_path = Path("output_tsv.tab")
            if not tsv_path.exists():
                tsv_path.touch()

            with open(tsv_path, "a") as file:
                file.write(tsv_string + "\n\n")

            console.print(
                "[spring_green3]> TSV file updated with new data[/spring_green3]"
            )

    def process(self, pdf_path: Path) -> str:
        """
        Processes an SAS Award PDF file and saves data to YAML and TSV output files.
        """

        with console.status(
            "[bright_cyan]Initializing data extraction...[/bright_cyan]"
        ) as status:
            # sleep(1)

            if not isinstance(pdf_path, Path):
                raise ValueError(
                    "File format mismatch:\n"
                    "Expected Type: Path\n"
                    f"Current Type: {type(pdf_path)}"
                )
            elif not pdf_path.exists():
                raise FileNotFoundError(f"File not found: {pdf_path}")
            elif pdf_path.suffix != ".pdf":
                raise ValueError(f"Invalid file type: {pdf_path.suffix}. Expected .pdf")
            status.stop()

            self.extract_data(pdf_path)
            self.populate_attrs()
            self.find_incomplete_fields()
            self.match_org_and_div()
            self.format_fields()
            self.categorize_amounts()
            self.validate_amounts()
            self.enforce_limits()
            self.save_yaml()
            self.save_tsv()

            console.print(
                "[spring_green3]> PDF processing and data transformation complete.[/spring_green3]"
            )

            pprint(self.output())

