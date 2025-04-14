import json
import shutil
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import sleep
from typing import Optional

import fitz
import yaml
from constants import (archive_path, consultant_map, json_output_path,
                       tsv_output_path)
from evaluator import AwardEvaluator
from formatting import Formatter
from rich.console import Console
from utils import LogID, find_mgmt_division, find_organization, logger

console = Console()


@dataclass
class IndProcessor:
    log_id: Optional[str] = None
    funding_org: Optional[str] = None
    employee_name: Optional[str] = "employee_name"
    monetary_amount: Optional[int] = None
    time_off_amount: Optional[int] = None
    employee_org: Optional[str] = "organization"
    employee_pay_plan: Optional[str] = "pay_plan_gradestep_1"
    employee_supervisor_name: Optional[str] = "please_print_2"
    employee_supervisor_org: Optional[str] = "org_3"
    nominator_name: Optional[str] = "please_print"
    nominator_org: Optional[str] = "org"
    sas_monetary_amount: Optional[str] = "undefined"
    sas_time_off_amount: Optional[str] = "hours_2"
    ots_monetary_amount: Optional[str] = "on_the_spot_award"
    ots_time_off_amount: Optional[str] = "hours"
    certifier_name: Optional[str] = "special_act_award_funding_string_2"
    certifier_org: Optional[str] = "org_2"
    approver_name: Optional[str] = "please_print_3"
    approver_org: Optional[str] = "org_4"
    administrator_name: Optional[str] = "please_print_4"
    reviewer_name: Optional[str] = "please_print_5"
    funding_string: Optional[str] = "special_act_award_funding_string_1"
    mb_division: Optional[str] = None
    justification: Optional[str] = "extent_of_application"
    value: Optional[str] = None
    extent: Optional[str] = None
    category: Optional[str] = "IND"
    type: Optional[str] = None
    date_received = datetime.now().strftime("%Y-%m-%d")

    def __str__(self) -> None:
        attributes = {
            "Log ID": self.log_id,
            "Funding Org": self.funding_org,
            "Monetary Amount": f"${self.monetary_amount}",
            "Time-Off Amount": f"{self.time_off_amount} hours",
            "Employee Name": self.employee_name,
            "Employee Org": self.employee_org,
            "Nominator Name": self.nominator_name,
            "Nominator Org": self.nominator_org,
            "Justification": f"{len(self.justification.split())} words",
            "Value": self.value.capitalize(),
            "Extent": self.extent.capitalize(),
            "Category": self.category,
            "Type": self.type,
            "Date Received": self.date_received,
            "HRC": self.consultant,
        }

        return "\n".join(f"{key}: {value}" for key, value in attributes.items())

    def extract_data(self) -> dict[str, Optional[str]]:
        """
        Extracts the data from the PDF file using PyMuPDF.
        """
        with console.status("[bright_cyan]Extracting data from PDF...[/bright_cyan]"):
            # sleep(0.75)

            pdf_data = {}
            with fitz.open(self.pdf_path) as doc:
                for page in doc:
                    for field in page.widgets():
                        key = Formatter(field.field_name).key()
                        val = Formatter(field.field_value).value()
                        pdf_data[key] = val

            if not pdf_data:
                raise ValueError("No data extracted from the PDF.")

            console.print("[spring_green3]> Data extracted from PDF[/spring_green3]")

            return pdf_data

    def populate_attrs(self, award_data: dict[str, Optional[str]]) -> None:
        """
        Populates the class attributes with the extracted data.
        """
        with console.status("[bright_cyan]Populating attributes...[/bright_cyan]"):
            # sleep(0.75)

            exempt_attr_fields: list[str] = [
                "funding_org",
                "monetary_amount",
                "time_off_amount",
                "mb_division",
                "value",
                "extent",
                "category",
                "type",
                "date_received",
                "log_id",
                "pdf_path",
            ]
            for field_name, placeholder_value in self.__dict__.items():
                if field_name in exempt_attr_fields:
                    continue

                field_value = award_data.get(placeholder_value, None)
                setattr(self, field_name, field_value)

            value_options: list[str] = [
                k
                for k, v in award_data.items()
                if k in AwardEvaluator.value_options and str(v).lower() == "on"
            ]
            self.value = value_options[0] if len(value_options) == 1 else self.value

            extent_options: list[str] = [
                k
                for k, v in award_data.items()
                if k in AwardEvaluator.extent_options and str(v).lower() == "on"
            ]
            self.extent = extent_options[0] if len(extent_options) == 1 else self.extent

            console.print("[spring_green3]> Populated attributes[/spring_green3]")

    def initial_validation(self) -> list[str]:
        """
        Validates that required fields are populated.
        """
        with console.status(
            "[bright_cyan]Validating required fields...[/bright_cyan]"
        ) as status:
            # sleep(0.75)

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
                field for field in required_fields if getattr(self, field, None) is None
            ]
            if incomplete_fields:
                status.stop()
                incomplete_fields = yaml.safe_dump(incomplete_fields, indent=4)
                incomplete_msg: str = f"Missing Fields:\n{incomplete_fields}"
                console.print(f"[bright_red]{incomplete_msg}[/bright_red]")

            options = {1: "Continue", 9: "Skip"}
            selection: int
            while True:
                try:
                    console.print(
                        "[orange1]\n"
                        "Make a selection:\n"
                        "1: Continue processing.\n"
                        "9: Skip this award."
                        "[/orange1]"
                    )
                    selection = int(input("> ").strip())
                    if selection not in options:
                        raise ValueError("Selection must be 1 or 9.")
                    if selection in options:
                        break
                except Exception as e:
                    console.print(f"[bright_red]Invalid selection. {e}[/bright_red]")
            if selection == 9:
                raise ValueError(f"Unable to proceed with processing. {incomplete_msg}")

            if "es" in self.employee_pay_plan.lower():
                raise ValueError(
                    f"'ES' pay plans not allowed: {self.employee_pay_plan}"
                )

            console.print(
                "[spring_green3]> All required fields are populated[/spring_green3]"
            )

    def parse_org_divs(self):
        """
        Matches the funding organization based on the values of the organization fields.
        """
        with console.status("[bright_cyan]Matching organization...[/bright_cyan]"):
            # sleep(0.75)

            org_fields = [
                "employee_org",
                "employee_supervisor_org",
                "nominator_org",
                "certifier_org",
                "approver_org",
            ]

            for field in org_fields:
                try:
                    if (search_val := getattr(self, field, None)) is not None:
                        if (
                            div_match := find_organization(search_val, get_div=True)
                        ) is not None:
                            setattr(self, field, div_match)
                except:
                    pass

            processed_divs = [
                div
                for div in [
                    self.employee_org,
                    self.nominator_org,
                    self.certifier_org,
                    self.employee_supervisor_org,
                    self.approver_org,
                ]
                if div
            ]

            org_counter = Counter(
                [find_organization(org) for org in processed_divs]
            ).most_common(1)
            self.funding_org = org_counter[0][0] if org_counter else None

            if self.funding_org is None:
                raise ValueError("Unable to determine funding org.")

            self.consultant: str = consultant_map[self.funding_org]

            console.print(
                f"[spring_green3]> Funding org set to '{self.funding_org}'[/spring_green3]"
            )

            if "mb" in self.funding_org.lower():
                try:
                    mb_div_list = [
                        find_mgmt_division(getattr(self, org))
                        for org in org_fields
                        if getattr(self, org, None) is not None
                    ]
                    processed_mb_list = [div for div in mb_div_list if div is not None]
                    self.mb_division = (
                        Counter(processed_mb_list).most_common(1)[0][0]
                        if processed_mb_list
                        else None
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
            # sleep(0.75)

            name_fields = [
                "employee_name",
                "nominator_name",
                "certfier_name",
                "employee_supervisor_name",
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
                    v = Formatter(v).justification()
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
            # sleep(0.75)

            sas_fields = [
                "sas_monetary_amount",
                "sas_time_off_amount",
            ]
            sas_values = [
                getattr(self, field)
                for field in sas_fields
                if getattr(self, field, None) is not None
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
        ) as status:
            # sleep(0.75)

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
                "[spring_green3]> Award amounts meet the required criteria for further processing.[/spring_green3]"
            )

            eval_results = AwardEvaluator(
                self.value, self.extent, self.monetary_amount, self.time_off_amount
            ).evaluate()
            console.print(eval_results)

    def save_json(self) -> None:
        """
        Saves all award data to a JSON file.
        """
        with console.status("[bright_cyan]Saving data to JSON file...[/bright_cyan]"):
            # sleep(0.75)

            if not json_output_path.exists():
                json_output_path.write_text(r"[]")

            with open(json_output_path, "r", encoding="utf-8") as file:
                content: str = file.read().strip()
                content = r"[]" if not content else content

                json_dict_list: list[dict[str, str | int | None]] = json.loads(content)
                json_dict_list = [] if not json_dict_list else json_dict_list

            items: dict[str, str, int] = {
                k: v
                for k, v in self.__dict__.items()
                if not any(k.startswith(i) for i in ("sas", "ots"))
            }
            items["justification"] = f"{len(items['justification'].split())} words"
            items["pdf_path"] = self.pdf_path.name

            duplicates: list[dict] = [
                json_dict_item
                for json_dict_item in json_dict_list
                if json_dict_item.get("log_id", None) == self.log_id
            ]
            if duplicates:
                raise ValueError(
                    f"Duplicate entries found for Log ID {self.log_id}\n"
                    f"Duplicate count: {len(duplicates)}"
                )

            json_dict_list.append(items)

            with open(json_output_path, "w", encoding="utf-8") as file:
                json.dump(json_dict_list, file, indent=4, sort_keys=False)

            console.print(
                f"[spring_green3]> '{json_output_path.name}' updated with new data[/spring_green3]"
            )

    def save_tsv(self) -> None:
        """
        Saves specified data to a TSV file.
        """
        with console.status("[bright_cyan]Saving data to TSV file...[/bright_cyan]"):
            # sleep(0.75)
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
                self.value.capitalize(),
                self.extent.capitalize(),
            ]
            for idx, item in enumerate(tsv_items):
                if item is None:
                    tsv_items[idx] = "-"
                else:
                    tsv_items[idx] = str(item)

            tsv_string = "\t".join(tsv_items)

            if not tsv_output_path.exists():
                tsv_output_path.touch()

            with open(tsv_output_path, "a", encoding="utf-8") as file:
                file.write(tsv_string + "\n")

            console.print(
                f"[spring_green3]> '{tsv_output_path.name}' updated with new data[/spring_green3]"
            )

    def rename_and_copy_file(self) -> None:
        stem_items: list = [
            self.log_id,
            self.funding_org,
            self.employee_name,
            self.date_received,
        ]
        file_stem: str = " _ ".join(str(i) for i in stem_items)
        new_path: Path = self.pdf_path.with_stem(file_stem)
        renamed_path: Path = Path(self.pdf_path.rename(new_path))
        target_path: Path = archive_path / renamed_path.name
        try:
            shutil.copy2(renamed_path, target_path)
        except PermissionError:
            raise PermissionError(
                "Permission denied. The file is still open in another application. Please close the file and try again."
            )
        except Exception as e:
            print(f"Error renaming and copying file: {e}")

    def process(self, pdf_path: Path) -> str:
        """
        * Collects data from an SAS Award PDF file for processing
        * Saves data to YAML and TSV output files.
        * Renames local file.
        * Creates a copy of the file in the SAS FY Archive network folder.
        """

        with console.status(
            "[bright_cyan]Initializing data extraction...[/bright_cyan]"
        ) as status:
            # sleep(0.75)

            if not pdf_path.exists():
                raise FileNotFoundError(f"File not found: {pdf_path}")
            elif pdf_path.suffix != ".pdf":
                raise ValueError(f"Invalid file type: {pdf_path.suffix}. Expected .pdf")

            status.stop()

            self.pdf_path: Path = pdf_path
            self.log_id = LogID(self.category).get()

            data = self.extract_data()
            self.populate_attrs(data)
            self.initial_validation()
            self.parse_org_divs()
            self.format_fields()
            self.categorize_amounts()
            self.validate_amounts()
            self.save_json()
            self.save_tsv()
            self.rename_and_copy_file()
            LogID(self.category).save()

            console.print(
                "[spring_green3]> PDF processing and data transformation complete.[/spring_green3]"
            )
            logger(self)
            return self
