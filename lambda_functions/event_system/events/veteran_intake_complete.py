from datetime import datetime

from propus.helpers.input_validations import validate_email
from propus.logging_utility import Logging

from constants.hubspot_template_ids import (
    SCHEDULE_APPOINTMENT_TO_STUDENT,
    INTAKE_FORM_COMPLETE_TO_VS_TEAM,
)
from events.base import BaseEventSystem
from exceptions import (
    MultipleCalbrightEmailInSalesforce,
    CalbrightEmailNotInSalesforce,
)


class VeteranIntakeComplete(BaseEventSystem):
    __event_type__ = "veterans_intake_complete"
    _required_fields = [
        "form_id",
        "response_id",
        "intake_form_submitted",
        "calbright_email",
    ]

    _branch_of_service_map = {
        "US Army": "USA",
        "US Marine Corps": "USMC",
        "US Navy": "USN",
        "US Air Force": "USAF",
        "US Coast Guard": "USCG",
        "US National Guard": "USNG",
        "US Space Force": "USSF",
    }

    _formatted_fields = {
        "accessibility": "- Accessibility Services (Students with disabilities)",
        "tutoring": "- Tutoring/ Test preparation Supports",
        "mental_health": "- Calbright student's Mental Health/ Counseling Services",
        "career": "- Calbright Career and Vocational Services",
        "slack": "- Student Slack Community",
        "study_groups": "- Study groups/ Library / Exam prep",
        "study_skills": "- Study skills/ Career Services Workshops",
        "asg": "- Associated Student Government (ASG)",
        "dor_vocational": "- (DOR) Vocational/ Employment Services",
        "va_vocational": "- VA Vocational Rehabilitation and Employment Services",
        "va_ebenefits": "- VA eBenefits",
        "housing": "- Housing / Homelessness Services",
        "va_educational": "- VA Educational Benefits",
        "cal_vet": "- California Vet Benefits",
    }

    _form_keys = {
        "intake_form_submitted": {"lines": ["Intake Form Submitted At:"]},
        "response_id": {"lines": ["Response ID:"]},
        "branch_of_service": {"lines": ["Branch of Service:"], "type": "multi"},
        "status": {"lines": ["Status:"]},
        "program_of_study": {"lines": ["Program of Study:"]},
        "disabilities": {"lines": ["Do you have any disabilities?"]},
        "student_supports": {
            "lines": [
                "Which of the following Calbright student supports are you already connected",
                "  aware of and which are you interested in learning more about?",
            ],
            "type": "multi",
        },
        "community_support": {
            "lines": [
                "Please share which of the following supports or services are you already",
                "  connected with or are interested in learning more about:",
            ],
            "type": "multi",
        },
        "information": {
            "lines": ["What other information, services or resources are you interested in?"],
            "type": "text",
        },
        "addt_support": {
            "lines": [
                "What can we do or offer to build a strong and supportive online",
                "  Veteran's Community at Calbright?",
            ],
            "type": "text",
        },
    }
    _statuses = ["Reserve", "Discharged", "Dependent", "Active Duty"]
    _program_of_study = [
        "CRM Platform Administration",
        "IT Support",
        "Cybersecurity",
        "Data analysis",
        "Medical Coding",
        "Undecided",
    ]

    def __init__(self, configs, pdf, salesforce, hubspot, gdrive):
        super().__init__(configs)
        self.logger = Logging.get_logger("event/veteran_intake_complete")
        self.pdf_service = pdf
        self.salesforce = salesforce
        self.hubspot = hubspot
        self.gdrive = gdrive

        self.veteran_services_email = self.constants.get("email", {}).get("veterans", "veteran_services@calbright.org")
        self.google_drive_parent = configs.get("veteran_intake_complete").get("g_drive_parent_folder")

    @staticmethod
    def build(configs, ssm):
        from services.salesforce_client import SalesforceClient
        from services.hubspot_client import HubspotClient
        from services.gdrive_client import GoogleDriveClient
        from fpdf import FPDF

        return VeteranIntakeComplete(
            configs=configs,
            pdf=FPDF(),
            salesforce=SalesforceClient(configs.get("salesforce_ssm"), ssm),
            hubspot=HubspotClient(configs.get("hubspot_ssm"), ssm),
            gdrive=GoogleDriveClient(configs.get("gdrive_ssm"), ssm),
        )

    def run(self, event):
        self.check_required_fields(self.__event_type__, event, self._required_fields)
        validate_email(event.get("calbright_email"))

        salesforce_record = self.salesforce.custom_query(
            f"""Select Id, firstname, lastname, cfg_ccc_id__c, (Select Id From Veteran_Service_Records__r)
            FROM Contact WHERE cfg_Calbright_Email__c = '{event.get('calbright_email')}'"""
        )
        if salesforce_record.get("totalSize") == 0:
            self.logger.error(f"calbright email {event.get('calbright_email')} not in salesforce")
            raise CalbrightEmailNotInSalesforce(event.get("calbright_email"))
        if salesforce_record.get("totalSize") > 1:
            self.logger.error(f"multiple salesforce records found with calbright email {event.get('calbright_email')}")
            raise MultipleCalbrightEmailInSalesforce(event.get("calbright_email"))

        # Update Salesforce with all information filled out in intake form
        fields = [
            "intake_form_submitted",
            "status",
            "program_of_study",
            "disabilities",
            "student_supports",
            "community_support",
        ]
        payload = {field: event.get(field) for field in fields if event.get(field) is not None}
        if payload.get("program_of_study") not in self._program_of_study:
            payload["other_program_of_study"] = payload.get("program_of_study")
            payload["program_of_study"] = "Other"

        if event.get("branch_of_service"):
            branch_set = set()
            for branch in event.get("branch_of_service"):
                if self._branch_of_service_map.get(branch):
                    branch_set.add(self._branch_of_service_map.get(branch))
                else:
                    branch_set.add("Other")
                    payload["other_branch_of_service"] = branch
            payload["branch_of_service"] = list(branch_set)
        if payload.get("status") and payload.get("status") not in self._statuses:
            payload["status"] = "Other"
            payload["other_status"] = event.get("status")

        self.logger.info(f"updating veteran record for {event.get('calbright_email')}")
        self.create_intake_data_pdf(salesforce_record.get("records")[0], event)

        vet_records = salesforce_record.get("records")[0].get("Veteran_Service_Records__r")

        if vet_records is None:
            self.logger.warn(f"veteran record has not yet been created for {event.get('calbright_email')}")
            self.salesforce.create_vet_record(salesforce_record.get("records")[0].get("Id"), **payload)
        else:
            self.salesforce.update_vet_record(vet_records.get("records")[0].get("Id"), **payload)

        # # Email the Student to ask them to schedule a VS appointment
        self.hubspot.send_transactional_email(
            email_id=SCHEDULE_APPOINTMENT_TO_STUDENT,
            to_email=event.get("calbright_email"),
            email_name="VeteransServices: Schedule Appointment",
            salesforce_task={
                "client": self.salesforce,
                "task_data": {
                    "salesforce_id": salesforce_record.get("records")[0].get("Id"),
                    "activity_date": datetime.now().strftime("%Y-%m-%d"),
                    "status": "Completed",
                    "subject": "Emailed Veteran Services Appointment Link",
                    "description": "Student completed their intake form and an appointment request link was emailed",
                    "type": "Email",
                },
            },
        )

        self.hubspot.send_transactional_email(
            email_id=INTAKE_FORM_COMPLETE_TO_VS_TEAM,
            to_email=self.veteran_services_email,
            email_name="VeteransServices: Intake Form Submitted",
            custom_properties={
                "first_name": salesforce_record.get("records")[0].get("FirstName"),
                "last_name": salesforce_record.get("records")[0].get("LastName"),
                "ccc_id": salesforce_record.get("records")[0].get("cfg_CCC_ID__c"),
            },
        )

    # Create a PDF from the results from the intake form
    def create_intake_data_pdf(self, s_data, payload):
        def break_down_string(text):
            lines = []
            this_str = ""
            for word in text.split(" "):
                if this_str == "":
                    this_str = "     "
                this_str += f"{word} "
                if len(this_str) >= 75:
                    lines.append(this_str[:-1])
                    this_str = ""
            lines.append(this_str[:-1])
            return lines

        file_name = (
            "_".join(
                [
                    s_data.get("cfg_CCC_ID__c"),
                    s_data.get("FirstName"),
                    s_data.get("LastName"),
                    datetime.now().strftime("%Y%m%d%H%M"),
                ]
            )
            + ".pdf"
        )
        full_file_name = f"/tmp/{file_name}"
        self.pdf_service.add_page()
        self.pdf_service.set_font("Helvetica", size=12)

        lines = [f"{s_data.get('FirstName')} {s_data.get('LastName')} - CCC ID: {s_data.get('cfg_CCC_ID__c')}"]
        for key, question in self._form_keys.items():
            if not payload.get(key):
                continue
            if question.get("type") == "multi" or question.get("type") == "text":
                for line in question.get("lines"):
                    lines.append(f"{line}")

                answer_lines = payload.get(key, [])
                if question.get("type") == "text":
                    answer_lines = break_down_string(payload.get(key))
                for ans in answer_lines:
                    lines.append(f"    {self._formatted_fields.get(ans, ans)}")

            else:
                lines.append(f'{question.get("lines")[0]} {payload.get(key, "")}')

        for i, line in enumerate(lines):
            self.pdf_service.cell(200, 10, txt=line, ln=i, align="L")

        self.pdf_service.output(full_file_name)
        self.gdrive.upload_file(
            full_file_name,
            {"title": file_name, "parents": [{"id": self.google_drive_parent}]},
        )
