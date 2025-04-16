import json
import shutil
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import fitz
from constants import EvalManager, PathManager, consultant_map, testing_mode
from evaluator import AwardEvaluator
from formatting import Formatter
from logger import Logger
from rich.console import Console
from utils import LogID, ManualEntry, find_mgmt_division, find_organization

console = Console()
logger = Logger()


@dataclass
class BaseProcessor:
    source_path: Optional[Path] = None
    log_id: Optional[str] = None
    funding_org: Optional[str] = None
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
    category: Optional[str] = None
    type: Optional[str] = None
    date_received = datetime.now().strftime("%Y-%m-%d")
    consultant: Optional[str] = None


@dataclass
class IndProcessor(BaseProcessor):

    def __post_init__(self):
        self.category = "IND"
        self.employee_name: Optional[str] = "employee_name"
        self.monetary_amount: Optional[int] = None
        self.time_off_amount: Optional[int] = None
        self.employee_org: Optional[str] = "organization"
        self.employee_pay_plan: Optional[str] = "pay_plan_gradestep_1"
        self.employee_supervisor_name: Optional[str] = "please_print_2"
        self.employee_supervisor_org: Optional[str] = "org_3"
        self.nominator_name: Optional[str] = "please_print"
        self.nominator_org: Optional[str] = "org"
        self.sas_monetary_amount: Optional[str] = "undefined"
        self.sas_time_off_amount: Optional[str] = "hours_2"
        self.ots_monetary_amount: Optional[str] = "on_the_spot_award"
        self.ots_time_off_amount: Optional[str] = "hours"
        self.log_id = LogID(self.category).get()

    def __str__(self) -> None:
        attributes: dict[str, str | int | None] = {
            "Source": self.source_path,
            "Log ID": self.log_id,
            "Funding Org": self.funding_org,
            "Monetary Amount": self.monetary_amount,
            "Time-Off Amount": self.time_off_amount,
            "Employee Name": self.employee_name,
            "Employee Org": self.employee_org,
            "Employee Pay Plan": self.employee_pay_plan,
            "  Nominator Name": self.nominator_name,
            "  Nominator Org": self.nominator_org,
            "  Certifier Name": self.certifier_name,
            "  Certifier Org": self.certifier_org,
            "  Justification": self.justification,
            "  Value": self.value,
            "  Extent": self.extent,
            "  Category": self.category,
            "  Type": self.type,
            "  Date Received": self.date_received,
            "  HRC": self.consultant,
        }

        string_list: list[str] = []

        for key, val in attributes.items():
            try:
                if all([isinstance(val, str), " " not in val, "_" in val[:40]]):
                    val = None
            except:
                pass

            if val:
                if key == "Monetary Amount":
                    val = f"${val}"
                elif key == "Time-Off Amount":
                    val = f"{val} hours"
                elif key.strip() in ["Value", "Extent"]:
                    val = val.capitalize()
                elif key.strip() == "Justification":
                    val = f"{len(self.justification.split())} words"
                elif isinstance(val, Path):
                    val = val.name
            string_list.append(f"{key}: {val}")

        return "\n".join(string_list)

    def _extract_data(self) -> dict[str, Optional[str]]:
        """
        Extracts the data from the PDF file using PyMuPDF.
        """
        with console.status("[bright_cyan]Extracting data from PDF...[/bright_cyan]"):
            # sleep(1)

            pdf_data = {}
            with fitz.open(self.source_path) as doc:
                for page in doc:
                    for field in page.widgets():
                        key = Formatter(field.field_name).key()
                        val = Formatter(field.field_value).value()
                        pdf_data[key] = val

            if not pdf_data:
                raise ValueError("No data extracted from the PDF.")

        if "a_nominees_team_leadersupervisor_1" in pdf_data.keys():
            attributes: dict[str, str] = {
                "employee_pay_plan": "pay_plan_gradestep",
                "sas_monetary_amount": "amount",
                "sas_time_off_amount": "hours",
                "ots_monetary_amount": "amount_2",
                "ots_time_off_amount": "hours_2",
                "nominator_name": "nominators_name",
                "nominator_org": "organization_2",
                "employee_supervisor_name": "a_nominees_team_leadersupervisor_1",
                "employee_supervisor_org": "organization_3",
                "approver_name": "approving_officialdesignee_1",
                "approver_org": "organization_5",
                "reviewer_name": "compliance_review_completed_by_1",
                "reviewer_org": "organization_6",
                "justification": "extent_of_application_limited_extended_or_general",
            }
            for attr_name, placeholder_value in attributes.items():
                try:
                    setattr(self, attr_name, placeholder_value)
                except:
                    pass
        logger.info("Extracted data from PDF.")
        return pdf_data

    def _populate_attrs(self, award_data: dict[str, Optional[str]]) -> None:
        """
        Populates the class attributes with the extracted data.
        """
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
            "source_path",
        ]
        for field_name, placeholder_value in self.__dict__.items():
            if field_name in exempt_attr_fields:
                continue

            field_value = award_data.get(placeholder_value, None)
            setattr(self, field_name, field_value)

        value_options: list[str] = [
            k
            for k, v in award_data.items()
            if k in EvalManager.value_options and str(v).lower() == "on"
        ]
        self.value = value_options[0] if len(value_options) == 1 else None

        extent_options: list[str] = [
            k
            for k, v in award_data.items()
            if k in EvalManager.extent_options and str(v).lower() == "on"
        ]
        self.extent = extent_options[0] if len(extent_options) == 1 else None

        logger.info("Populated IndProcessor attributes.")

    def _validate_pay_plan(self):
        if "es" in str(self.employee_pay_plan).lower():
            raise ValueError(f"'ES' pay plans not allowed: {self.employee_pay_plan}")

    def _get_missing_fields(self):
        required_fields: list[str] = [
            "employee_name",
            "nominator_name",
            "employee_supervisor_name",
            "approver_name",
            "reviewer_name",
            "justification",
        ]
        return [
            field for field in required_fields if getattr(self, field, None) is None
        ]

    def _prompt_user_action(self, error_msg: str):
        logger.warning(error_msg)

        options = {1: "Continue", 9: "Skip"}
        while True:
            try:
                console.print(
                    "[orange1]\n"
                    "Make a selection:\n"
                    "1: Continue processing.\n"
                    "9: Skip this award."
                    "[/orange1]"
                )
                selection: int = int(input("> ").strip())
                if selection not in options:
                    raise ValueError("Selection must be 1 or 9.")
                break
            except Exception as e:
                console.print(f"[orange1]Invalid selection. {e}[/orange1]")
        if selection == 9:
            raise ValueError(f"Unable to proceed with processing. {error_msg}")

    def _validate_fields(self) -> list[str]:
        missing_fields: list[str] = self._get_missing_fields()
        if missing_fields:
            error_msg: str = f"Missing Fields:\n{missing_fields}".strip()
            self._prompt_user_action(error_msg)
        self._validate_pay_plan()

    def _parse_org_divs(self) -> None:
        with console.status("[bright_cyan]Matching organization...[/bright_cyan]"):
            org_attrs = [
                "employee_org",
                "employee_supervisor_org",
                "nominator_org",
                "certifier_org",
                "approver_org",
            ]
            org_matches = self._match_organizations(org_attrs)
            self._determine_funding_organization(org_matches)
            self._set_consultant()
            self._set_mb_division(org_attrs)

    def _match_organizations(self, org_attrs: list[str]) -> list[str]:
        """Match organizations for the given fields."""
        org_matches: list[str] = []
        for attr_name in org_attrs:
            try:
                org_field_value = getattr(self, attr_name, None)
                if org_field_value is not None:
                    org_match, div_match = find_organization(org_field_value)
                    attr_value = (
                        div_match if div_match else org_match if org_match else None
                    )
                    if attr_value is not None:
                        setattr(self, attr_name, attr_value)
                    org_matches.append(org_match) if org_match is not None else None

            except AttributeError as e:
                logger.error(f"Error processing field '{attr_name}': {e}")
        return org_matches

    def _determine_funding_organization(self, org_matches: list[str]) -> None:
        """Determine the funding organization based on the list of identified organizations."""
        org_counter = Counter(org_matches).most_common()
        self.funding_org = org_counter[0][0]

        if self.funding_org is None:
            raise ValueError("Unable to determine funding org.")

        logger.info(f"> Funding org set to '{self.funding_org}'")

    def _set_consultant(self) -> None:
        """Set the consultant based on the funding organization."""
        self.consultant = consultant_map.get(self.funding_org)
        if self.consultant is None:
            logger.warning(f"No consultant found for funding org '{self.funding_org}'")

    def _set_mb_division(self, org_attrs: list[str]) -> None:
        """Set the MB division if the funding organization contains 'mb'."""
        if "mb" not in str(self.funding_org).lower():
            return

        mb_div_list = []
        for attr_name in org_attrs:
            attr_value = getattr(self, attr_name, None)
            if attr_value:
                div_match = find_mgmt_division(attr_value)
                mb_div_list.append(div_match) if div_match else None

        if not mb_div_list:
            return

        self.mb_division = Counter(mb_div_list).most_common()[0][0]
        if self.mb_division is not None:
            logger.info(f"> MB division set to '{self.mb_division}'")

    def _format_fields(self) -> None:
        """
        "Prepares object fields for further processing by applying formatting rules."
        """
        with console.status("[bright_cyan]Formatting fields...[/bright_cyan]"):
            # sleep(1)

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

            logger.info("> All fields have been formatted")

    def _classify_amounts(self):
        """
        Categorizes award amounts as either SAS or OTS based on specific fields.
        """
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

        logger.info(f"Type set to {self.type}.")

    def _validate_amounts(self):
        """
        Confirms the award amounts meet the required criteria.
        """
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

        logger.info("Award amounts meet the required criteria for further processing.")

        try:
            evaluator = AwardEvaluator(
                self.value, self.extent, self.monetary_amount, self.time_off_amount
            )
            eval_results = evaluator.evaluate()
            logger.info(eval_results)
        except SyntaxError as se:
            logger.warning(se)

    def _validate_and_transform(self) -> None:
        self._validate_fields()
        self._parse_org_divs()
        self._format_fields()
        self._classify_amounts()
        self._validate_amounts()

    def _save_json(self) -> None:
        """
        Saves all award data to a JSON file.
        """
        with console.status("[bright_cyan]Saving data to JSON file...[/bright_cyan]"):
            # sleep(1)

            with open(PathManager.json_output_path, "r", encoding="utf-8") as file:
                content: str = file.read().strip()
                content = "[]" if not content else content

                json_dict_list: list[dict[str, str | int | None]] = json.loads(content)

            dict_items: dict[str, str | int] = {}
            for k, v in self.__dict__.items():
                if type(v) not in [str, int, float, None]:
                    v = str(v)
                dict_items[k] = v

            dict_items["justification"] = (
                f"{len(dict_items['justification'].split())} words"
            )
            try:
                dict_items["source_path"] = Path(dict_items["source_path"]).name
            except:
                pass

            duplicates: list[dict] = [
                json_dict_item
                for json_dict_item in json_dict_list
                if json_dict_item.get("log_id", None) == self.log_id
            ]
            if duplicates:
                logger.error(
                    f"Duplicate entries found for Log ID {self.log_id}\n"
                    f"Duplicate count: {len(duplicates)}"
                )
                exit()

            json_dict_list.append(dict_items)

            with open(PathManager.json_output_path, "w", encoding="utf-8") as file:
                json.dump(json_dict_list, file, indent=4, sort_keys=False)

            logger.info(
                f"> '{PathManager.json_output_path.name}' updated with new data"
            )

    def _save_tsv(self) -> None:
        """
        Saves specified data to a TSV file.
        """
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
            self.value.capitalize() if self.value else None,
            self.extent.capitalize() if self.extent else None,
        ]
        for idx, item in enumerate(tsv_items):
            if (
                id(item) == id(self.mb_division)
                and "mb" not in str(self.funding_org).lower()
            ):
                tsv_items[idx] = ""
            elif item is None:
                tsv_items[idx] = "-"
            else:
                tsv_items[idx] = str(item)

        tsv_string = "\t".join(tsv_items)

        with open(PathManager.tsv_output_path, "a", encoding="utf-8") as file:
            file.write(tsv_string + "\n")

        logger.info(f"> '{PathManager.tsv_output_path.name}' updated with new data")

    def _rename_and_copy_file(self) -> None:
        if testing_mode or not isinstance(self.source_path, Path):
            return
        stem_items: list = [
            self.log_id,
            self.funding_org,
            self.employee_name,
            self.date_received,
        ]
        file_stem: str = " _ ".join(str(i) for i in stem_items)
        new_path: Path = self.source_path.with_stem(file_stem)
        renamed_path: Path = Path(self.source_path.rename(new_path))
        target_path: Path = PathManager.archive_path / renamed_path.name
        try:
            shutil.copy2(renamed_path, target_path)
        except PermissionError:
            raise PermissionError(
                "Permission denied. The file is still open in another application. Please close the file and try again."
            )
        except Exception as e:
            print(f"Error renaming and copying file: {e}")
        renamed_path.unlink()

    def _save_and_log(self) -> None:
        """Save data in different formats and log the category."""
        self._save_json()
        self._save_tsv()
        self._rename_and_copy_file()
        LogID(self.category).save()

    def run_processing(
        self, source_path: Optional[Path] = None, manual_entry: bool = False
    ) -> None:

        if source_path is not None and manual_entry is False:
            self.source_path = source_path
            logger.path(self.source_path.name)
            data = self._extract_data()
            self._populate_attrs(data)
        self._validate_and_transform()
        self._save_and_log()

        logger.info("PDF processing and data transformation complete.")
        logger.final(self)

    def _apply_manual_attributes(self, manual_data: dict[str, str]) -> None:
        if manual_data:
            for attr_name, value in manual_data.items():
                formatted_value = Formatter(str(value)).value()
                setattr(self, attr_name, formatted_value)

    def _process_manual_input(self) -> None:
        print("\n", " Manual Entry Mode ".center(100, "-"), "\n")

        try:
            manual_entry_data = ManualEntry.load()
            self._apply_manual_attributes(manual_entry_data)
            self.run_processing(manual_entry=True)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    try:
        IndProcessor()._process_manual_input()
    except Exception as e:
        print(e)
