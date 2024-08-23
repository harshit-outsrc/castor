from copy import deepcopy
from datetime import datetime, timedelta
from typing import AnyStr, Dict, List
from zoneinfo import ZoneInfo

from propus.aws.ssm import AWS_SSM
from propus import Logging
from propus.gsuite import Sheets
from propus.salesforce import Salesforce

from services.salesforce_service import SalesforceService
from services.pdf_service import PdfService
from services.email_service import EmailService
from pace_exceptions import MissingRequiredHeader, GSheetIncorrectTabName

from const.crm_badge_progress_constants import (
    crm_timeline_60_day,
    crm_timeline_90_day,
    crm_timeline_120_day,
    crm_timeline_180_day,
    crm_timeline_365_day,
)

DATE_STRING_FMT = "%B %-d, %Y"


class PacePipeline:
    def __init__(self, configs, gsheet, salesforce_service, pdf_service, email_service):
        self.logger = Logging.get_logger("pace_pipeline.py")
        self.gsheet = gsheet
        self.worksheet = None
        self.salesforce_service = salesforce_service
        self.email_service = email_service
        self.configs = configs
        self.pdf_service = pdf_service
        dt = datetime.now(tz=ZoneInfo("America/Los_Angeles"))
        self.run_date = dt.replace(hour=23, minute=59, second=59)
        self.required_headers = [
            "CCC ID",
            "First Name",
            "Last Name",
            "Timeline",
            "Enrollment Date",
            "Grace Period",
            "Auto Grace Period",
        ]
        self.stopout_week = 7

        self.milestones_by_timeline = {
            "90 Day": [1, 2, 3, 4, 5, 9, 13],
            "120 Day": [1, 2, 3, 4, 5, 6, 7, 12, 18],
            "180 Day": [1, 2, 3, 5, 6, 7, 8, 9, 10, 18, 26],
            "365 Day": [1, 2, 3, 5, 6, 9, 10, 12, 13, 14, 15, 16, 17, 18, 19, 34, 52],
        }

        self.week_crm_badges = {
            "60 Day": crm_timeline_60_day,
            "90 Day": crm_timeline_90_day,
            "120 Day": crm_timeline_120_day,
            "180 Day": crm_timeline_180_day,
            "365 Day": crm_timeline_365_day,
        }

    @staticmethod
    def build(configs):
        ssm = AWS_SSM.build()
        return PacePipeline(
            configs=configs,
            gsheet=Sheets.build(ssm.get_param(configs.get("ssm").get("gsheet"), param_type="json")),
            salesforce_service=SalesforceService(
                Salesforce.build(**ssm.get_param(configs.get("ssm").get("salesforce"), param_type="json"))
            ),
            pdf_service=PdfService.build(configs, ssm.get_param(configs.get("ssm").get("gdrive"))),
            email_service=EmailService.build(configs, ssm),
        )

    @staticmethod
    def build_tdd(configs):
        from mock_classes.salesforce import MockSalesforce

        ssm = AWS_SSM.build()
        return PacePipeline(
            configs=configs,
            gsheet=Sheets.build(ssm.get_param(configs.get("ssm").get("gsheet"), param_type="json")),
            salesforce_service=SalesforceService(MockSalesforce()),
            pdf_service=PdfService.build(configs, ssm.get_param(configs.get("ssm").get("gdrive"))),
            email_service=EmailService.build(configs, ssm),
        )

    def fetch_pdf_args(self, timeline: AnyStr, contact_data: Dict) -> Dict:
        """
        This function uses the timeline and contact data and gathers all arguments needed to create the
        initial plan pdf.

        Args:
            timeline (AnyStr): String of the Timeline the student is on (i.e. 90 Day)
            contact_data (Dict): Dictionary with key/value data of student data

        Returns:
            Dict: Arguments needed for the PDF that is dynamically created for the student
        """
        args = {
            "full_name": f"{contact_data.get('first_name', '')} {contact_data.get('last_name', '')}",
            "enrollment_date": contact_data.get("enrollment_date").strftime(DATE_STRING_FMT),
            "timeline": timeline,
        }

        for week in self.milestones_by_timeline.get(timeline):
            date_string = (contact_data.get("enrollment_date") + timedelta(days=week * 7)).strftime(DATE_STRING_FMT)
            args[f"week_{week}"] = date_string
            if not args.get("first_completion_date"):
                args["first_completion_date"] = date_string

        return args

    def handle_enrolled_yesterday(self, ccc_id: AnyStr, timeline: Dict, contact_record: Dict) -> None:
        """
        If a student enrolled yesterday this function will send the initial timeline onboarding email which
        include the link to the plan PDF with milestones. This function creates that PDF, Uploads it to S3 static
        bucket, and sends the email.

        Args:
            ccc_id (AnyStr): Student's CCCID
            timeline (Dict): Timeline data (i.e. tract 90 Day, 120 Day)
            contact_record (Dict): Student contact record data
        """
        pdf_args = self.fetch_pdf_args(timeline, contact_record)
        document_url = self.pdf_service.generate_and_upload_pdf(ccc_id, pdf_args)
        self.email_service.send_welcome_email(
            timeline=timeline,
            contact_record=contact_record,
            doc_url=document_url,
            completion_date=pdf_args.get("first_completion_date"),
            competency_list=self.week_crm_badges.get(timeline).get("week1"),
        )

    @staticmethod
    def fetch_competencies_needed_for_completion(week_number: int, weekly_competencies: Dict) -> Dict:
        """
        This function uses the week number that the student is on and figures out which competencies
        they should have completed by this milestone and also figures out which competencies
        they should complete in the future.

        Args:
            week_number (int): integer of the week number the student is on
            weekly_competencies (Dict): dictionary of weeks to list of competencies that should have been completed
                - i.e. {"week1": ["comp1", "comp2", "comp3", "comp4"]...}

        Returns:
            Dict: Dictionary of Competency Data. Explanation of keys and values:
                - week_number: integer of the week the student is on. Same as the variable passed in and only
                    supplied for down stream processes
                - prev_competencies: List of competencies that should have been completed already
                - prev_competencies_by_week: Dictionary of week to competencies that should have already been completed
                - mid_comps: Current open competencies (i.e student is on week 3 of a milestone that spans week 2-4)
                - future_comp: List of competencies that need to be completed in the future
                - prev_competencies_by_week: Dictionary of week to competencies that will need to be completed
        """
        future_comp, competencies = [], []
        future_comp_by_week, competencies_by_week = {}, {}
        mid_milestone = False
        mid_comps = []
        for i in range(int(list(weekly_competencies.keys())[-1][4:])):
            if weekly_competencies.get(f"week{i+1}"):
                if i < week_number:
                    competencies += weekly_competencies.get(f"week{i+1}", [])
                    competencies_by_week[i + 1] = weekly_competencies.get(f"week{i+1}")
                else:
                    if not mid_comps and mid_milestone:
                        mid_comps = weekly_competencies.get(f"week{i+1}")
                    future_comp_by_week[i + 1] = weekly_competencies.get(f"week{i+1}")
                    future_comp += weekly_competencies.get(f"week{i+1}")
            elif i + 1 == week_number:
                mid_milestone = True
        return {
            "week_number": week_number + 1,  # This is now the effective week (new week)
            "prev_competencies": competencies,
            "prev_competencies_by_week": competencies_by_week,
            "mid_comps": mid_comps,
            "future_comp": future_comp,
            "future_comp_by_week": future_comp_by_week,
        }

    def fetch_badge_statuses(self, comp_data: Dict, completed_badges: List[Dict], completed_week_num: int) -> Dict:
        """
        This function parses the user's competency data, badges completed and the current week completed and
        returns the list of  incomplete competencies that should have been completed by their timeline, all
        completions, and the current number of weeks behind a student is on their timeline

        Args:
            comp_data (Dict): Dictionary response from fetch_competencies_needed_for_completion
            completed_badges (List[Dict]): list of dictionaries containing all badges completed by the student
            completed_week_num (int): the week number that the student just completed

        Returns:
            Dict: dictionary containing the following keys:
                incomplete_competencies -> competencies that should have been completed but have not been yet
                all_completions -> list of all competencies a student has completed
                latest_completion - > datetime of the last completion the student did
                weeks_behind -> integer of the weeks behind a student is
        """
        all_completed = []
        all_badges = comp_data.get("prev_competencies") + comp_data.get("future_comp")
        incomplete_competencies = deepcopy(comp_data.get("prev_competencies"))
        latest_comp_dt = None

        for b_data in completed_badges:
            if b_data.get("badge_name") not in all_badges:
                continue
            all_completed.append(b_data.get("badge_name"))
            if latest_comp_dt is None or b_data.get("completion_datetime") > latest_comp_dt:
                latest_comp_dt = b_data.get("completion_datetime")
            if b_data.get("badge_name") in incomplete_competencies:
                incomplete_competencies.remove(b_data.get("badge_name"))

        weeks_behind = 0
        prev_completed_competency = 0
        if incomplete_competencies:
            for week, competencies in comp_data.get("prev_competencies_by_week").items():
                if len(set(competencies).intersection(incomplete_competencies)) > 0:
                    weeks_behind = completed_week_num - prev_completed_competency
                    break
                else:
                    prev_completed_competency = week

        return {
            "incomplete_competencies": incomplete_competencies,
            "all_completions": all_completed,
            "latest_completion": latest_comp_dt,
            "weeks_behind": weeks_behind,
        }

    def fetch_week_number(self, enrollment_date: datetime, timeline_weeks: List) -> (int, datetime):
        """
        Given a student's enrollment date and a list of all weeks that are milestone weeks this function
        calculates the student's current week number as well as their next milestone date

        Args:
            enrollment_date (datetime): datetime of student's enrollment date
            timeline_weeks (List): List of milestone weeks for a given timeline tract

        Returns:
            week: an integer of the week number the student is one
            next_milestone_date: datetime of the next milestone the student should achieve
        """
        week = (self.run_date - enrollment_date).days // 7
        next_completion = timeline_weeks[-1]
        for rem_week in timeline_weeks:
            if rem_week > week:
                next_completion = rem_week
                break
        next_milestone_date = enrollment_date + timedelta(days=next_completion * 7)
        return week, next_milestone_date

    def handle_weekly_update(self, timeline_data: Dict, contact_record: Dict):
        """
        This function will handle the sending of an automated email for a weekly update. It takes in the student's
        data (contact record) and the timeline data to determine the correct email to send to the student.

        Args:
            timeline_data (Dict): Dictionary of timeline specific data
            contact_record (Dict): Dictionary of contact record data from Salesforce
        """
        week_number, next_completion_date = self.fetch_week_number(
            enrollment_date=contact_record.get("enrollment_date"),
            timeline_weeks=self.milestones_by_timeline.get(timeline_data.get("Timeline")),
        )
        comp_data = self.fetch_competencies_needed_for_completion(
            week_number, self.week_crm_badges.get(timeline_data.get("Timeline"))
        )

        self.logger.info(
            f"CCC ID: {timeline_data.get('CCC ID')} finished week {week_number} on {timeline_data.get('Timeline')}"
        )
        if contact_record.get("learner_status") == "Enrolled in Program Pathway":
            """
            If a student is still in EPP then we send out a specific email to them for 2 weeks and then stop sending
            additional emails as the student will get dropped
            """
            if week_number > 2:
                return
            self.email_service.send_epp_email(contact_record, timeline_data.get("Timeline"), comp_data)
            return

        user_id = self.salesforce_service.fetch_trailhead_user_data(contact_record.get("id"))

        badge_data = self.salesforce_service.fetch_user_badges(user_id)

        user_badge_data = self.fetch_badge_statuses(comp_data, badge_data, week_number)

        if 1 < user_badge_data.get("weeks_behind") <= 6 and timeline_data.get("Auto Grace Period") != "TRUE":
            self.gsheet.update_cell(
                self.worksheet,
                "TRUE",
                row_num=timeline_data.get("way_back_cell").get("row"),
                cell_num=timeline_data.get("way_back_cell").get("col"),
            )
            self.gsheet.update_cell(
                self.worksheet,
                int(timeline_data.get("Grace Period", 0)) + 2,
                row_num=timeline_data.get("way_back_cell").get("row"),
                cell_num=timeline_data.get("way_back_cell").get("col") - 1,
            )
            # Set Grace Period to Enrollment Date
            contact_record["enrollment_date"] = contact_record.get("enrollment_date") + timedelta(days=14)
            # Fetch new Week and Next Milestone Date
            week_number, next_completion_date = self.fetch_week_number(
                enrollment_date=contact_record.get("enrollment_date"),
                timeline_weeks=self.milestones_by_timeline.get(timeline_data.get("Timeline")),
            )
        elif user_badge_data.get("weeks_behind") >= self.stopout_week:
            if user_badge_data.get("weeks_behind") == self.stopout_week:
                self.email_service.send_stopout_email(contact_record)
            return

        self.email_service.send_weekly_update(
            contact_record, timeline_data, next_completion_date, comp_data, user_badge_data
        )

    def check_headers(self, headers):
        for header in self.required_headers:
            if header not in headers:
                self.logger.error(f"{header} is not in the google sheets header and execution has stopped")
                raise MissingRequiredHeader(header)

    def fetch_worksheet_data(self):
        all_ccc_ids = set()
        gsheet_url = self.configs.get("gsheet").get("url")

        response = []
        for gsheet_tab in self.configs.get("gsheet").get("tabs"):
            this_worksheet = self.gsheet.fetch_sheet(url=gsheet_url, sheet_tab=gsheet_tab)
            if this_worksheet.title not in self.configs.get("gsheet").get("expected_tab_names"):
                self.logger.error(f"Worksheet Retrieved ({this_worksheet.title}) does not match expected. Quitting")
                raise GSheetIncorrectTabName(this_worksheet.title)
            tab_rows = this_worksheet.get_values()
            tab_headers = tab_rows[0]
            self.check_headers(tab_headers)
            row_dict = []
            for row in tab_rows[1:]:
                if row[tab_headers.index("CCC ID")] in all_ccc_ids:
                    continue
                all_ccc_ids.add(row[tab_headers.index("CCC ID")])
                row_dict.append({tab_headers[idx]: row[idx] for idx in range(len(tab_headers))})
            response.append({"worksheet": this_worksheet, "timeline_data": row_dict})
        return all_ccc_ids, response

    def run_pipeline(self):
        ccc_ids, worksheet_data = self.fetch_worksheet_data()
        contact_dict = self.salesforce_service.fetch_bulk_contact_data(ccc_ids)

        matching_dates = 0
        row_count = 0
        for tab in worksheet_data:
            self.worksheet = tab.get("worksheet")
            row_count += len(tab.get("timeline_data"))
            matching_dates += self.process_students(tab.get("timeline_data"), contact_dict)
        self.logger.info(f"Completed Processing {row_count} rows and processed {matching_dates} matching date rows")

    def process_students(self, worksheet_data, contact_dict):
        matching_dates = 0

        for idx, row_dict in enumerate(worksheet_data):
            ccc_id = row_dict.get("CCC ID")

            if row_dict.get("TDD_CASE"):
                # TDD (Test Driven Development) is only used for development to map to Mock Requests and Data
                self.salesforce_service.update_tdd(
                    f"{row_dict.get('TDD_CASE')}_{row_dict.get('Timeline').replace(' ', '_')}"
                )

            if row_dict.get("Timeline") not in self.milestones_by_timeline:
                self.logger.warn(f"No Timeline Data For Row: {row_dict}")
                continue

            contact_info = contact_dict.get(ccc_id)
            if contact_info is None:
                self.logger.warn(f"no matching student with CCC ID: {ccc_id} in EPP and SPP")
                continue

            if contact_info.get("program") != "T2T CRM Admin":
                self.logger.warn(f"student not in CRM Program {ccc_id}")
                continue

            row_dict["way_back_cell"] = {"row": (idx + 2), "col": 7}
            if not row_dict.get("Grace Period"):
                row_dict["Grace Period"] = 0

            days_enrolled = (self.run_date - contact_info.get("enrollment_date")).days
            if days_enrolled == 1:
                self.handle_enrolled_yesterday(ccc_id, row_dict.get("Timeline"), contact_info)
                matching_dates += 1
            elif days_enrolled % 7 == 0 and days_enrolled > 0:
                if row_dict.get("Grace Period") and int(row_dict.get("Grace Period")) != 0:
                    contact_info["enrollment_date"] = contact_info.get("enrollment_date") + timedelta(
                        days=int(row_dict.get("Grace Period")) * 7
                    )
                self.handle_weekly_update(row_dict, contact_info)
                matching_dates += 1
        return matching_dates
