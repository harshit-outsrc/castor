from datetime import datetime, timezone
import json
import os
import re
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from typing import Dict, AnyStr

from propus.helpers.input_validations import validate_email
from propus.logging_utility import Logging
from propus.calbright_sql.enrollment_status import EnrollmentStatus
from propus.calbright_sql.enrollment_counselor import EnrollmentCounselor
from propus.calbright_sql.student import Student
from propus.calbright_sql.student_form import StudentForm, FormStatus, FormType
from propus.calbright_sql.user import User
from propus.helpers.sql_calbright.program import fetch_courses_for_program
from propus.helpers.sql_calbright.enrollment import upsert_enrollment, fetch_program_version_by_course_versions
from propus.helpers.sql_calbright.term_grades import upsert_eotg_records
from propus.helpers.sql_alchemy import update_or_create
from propus.calbright_sql.enrollment import LMS
from propus.calbright_sql.learner_status import LearnerStatus

from events.base import BaseEventSystem
from exceptions import CalbrightEmailNotInSalesforce, CccIdNotInDatabase
from constants.hubspot_template_ids import (
    CONTINUE_SERVICES_TO_STUDENT,
    CONTINUE_SERVICES_TO_VS_TEAM,
)

from events.constants import (
    INTENDED_PROGRAM_SLACK_TABLE,
    PROGRAM_API_VALUE_MAP,
    STRUT_COMPETENCY_IDS,
    EXISTING_COMPETENCY_IDS_CHECK,
    PROGRAM_PRODUCT_IDS,
    EXISTING_COMPLETION_PRODUCT_IDS,
    COURSE_CODES_TABLE,
    VALID_LEARNER_STATUS,
    CANVAS_LAUNCH_DATES_BY_PROGRAM,
)

# Custom Exceptions for this event


class MissingAcademicCounselorInDb(Exception):
    """Exception raised for missing Academic Counselor for student in Database"""

    def __init__(self, sf_id):
        super().__init__(f"ASC with ID {sf_id} not in calbright DB")


class MissingAcademicCounselor(Exception):
    """Exception raised for missing Academic Counselor for student in Salesforce"""

    def __init__(self, ccc_id):
        super().__init__(f"No ASC is assigned for {ccc_id}")


class SalesforceProgramEnrollmentError(Exception):
    """Exception raised for failing to create salesforce program enrollment"""

    def __init__(self, ccc_id):
        super().__init__(f"Failed to create salesforce program enrollment for {ccc_id}")


class InstructorNotInDatabase(Exception):
    """Exception raised for no matching instructor found in the database"""

    def __init__(self, instructor):
        super().__init__(f"Salesforce Instructor {instructor} not found in database")


class CsepComplete(BaseEventSystem):
    __event_type__ = "csep_complete"

    _required_fields = ["id", "tokens", "date_modified", "fields"]
    _required_tokens = ["Student.CCCID", "Student.CalbrightEmail", "Student.ProgramName"]

    _form_bucket = None

    def __init__(self, configs, calbright, salesforce, slack, hubspot, strut, gsheets, sqs, canvas):
        super().__init__(configs)
        self.logger = Logging.get_logger("castor/lambda_functions/event_system/event/csep_complete")
        self.calbright = calbright
        self.canvas = canvas
        self.salesforce = salesforce
        self.hubspot = hubspot
        self.strut = strut
        self.slack = slack
        self.gsheets = gsheets
        self.sqs = sqs
        self.datetime_now = datetime.now(timezone.utc)  # Using UTC standard for other systems
        self.datetime_now_isoformat = self.datetime_now.isoformat()

        self.veteran_services_email = configs.get("veteran_services_email")
        self.veteran_services_intake_request_email_id = configs.get("csep_complete").get(
            "veteran_services_intake_request_id"
        )
        self.csep_complete_email_id = configs.get("csep_complete").get("csep_complete_email_id")
        self._form_bucket = configs.get("form_bucket")
        self.override_canvas = configs.get("override_canvas")
        self.orientation_section_id = configs.get("canvas_orientation_section")

    @staticmethod
    def build(configs, ssm):
        from services.calbright_client import CalbrightClient
        from services.canvas_client import CanvasClient
        from services.gsheets_client import GoogleSheetsService
        from services.hubspot_client import HubspotClient
        from services.salesforce_client import SalesforceService
        from services.slack_client import SlackService
        from services.strut_client import StrutClient
        from propus.aws.sqs import AWS_SQS

        return CsepComplete(
            configs=configs,
            calbright=CalbrightClient(configs.get("calbright_write_ssm"), ssm),
            salesforce=SalesforceService(configs.get("salesforce_ssm"), ssm),
            hubspot=HubspotClient(configs.get("hubspot_ssm"), ssm),
            gsheets=GoogleSheetsService(configs.get("gsheets_ssm"), ssm, configs.get("gsheets_keys")),
            slack=SlackService(configs.get("slack_ssm"), ssm),
            strut=StrutClient(configs.get("strut_ssm"), ssm),
            sqs=AWS_SQS.build(),
            canvas=CanvasClient(configs.get("canvas_ssm"), ssm),
        )

    def run(self, event_data):
        self.signed_datetime = event_data.get("date_modified")
        student_data, extra_data = self.validate_csep_data(event_data)
        pd_requests = self.get_csep_requests(event_data)
        self.logger.info(f"Grabbed PandaDoc Request for: {student_data.user.calbright_email}.")

        recipients = event_data.get("recipients")
        document_link = recipients[0].get("shared_link") if recipients else None
        current_term_data = self.salesforce.get_next_term(event_data.get("date_modified"))

        slack_channel = (
            INTENDED_PROGRAM_SLACK_TABLE.get("DEV_SLACK")
            if os.environ.get("ENV") in ("dev", "stage")
            else INTENDED_PROGRAM_SLACK_TABLE.get(extra_data.get("intended_program"), "enrollment_agreement")
        )

        self.slack.alert_student_signed_csep(
            channel=slack_channel,
            info={
                "intended_program": extra_data.get("intended_program"),
                "name": f"{student_data.user.first_name} {student_data.user.last_name}",
                "ccc_id": student_data.ccc_id,
                "id": student_data.user.salesforce_id,
            },
        )

        self.salesforce.client.update_contact_record(
            student_data.user.salesforce_id,
            Date_of_Enrollment__c=event_data.get("date_modified"),
            cfg_Learner_Status__c="Completed CSEP" if extra_data.get("is_crm") else "Enrolled in Program Pathway",
            cfg_Learner_Access_Services_Requested__c=pd_requests.get("accessibility_services"),
            LMS__c=extra_data.get("lms"),
            Current_Term__c=current_term_data.get("Id"),
            CSEP_Signed_Date__c=event_data.get("date_modified"),
            cfg_Intended_Program__c=extra_data.get("intended_program"),
            Veterans_Services_Requested__c=pd_requests.get("veterans_services"),
        )

        student_data.user.learner_status = self.calbright.session.execute(
            select(LearnerStatus).filter_by(
                status="Completed CSEP" if extra_data.get("is_crm") else "Enrolled in Program Pathway"
            )
        ).scalar_one()
        self.calbright.session.commit()

        course_versions = None
        if extra_data.get("lms") == "Strut":
            self.enroll_student_in_strut(
                student_data,
                extra_data.get("intended_program"),
                extra_data.get("cfg_Assigned_Learner_Advocate__r").get("Strut_User_ID__c"),
            )
        elif extra_data.get("lms") == "myTrailhead":
            course_versions = self.enroll_student_in_trailhead(
                student_data, extra_data.get("customer_community_user_created__c")
            )

        new_enrollment = self.create_enrollment_objects(
            student_data,
            extra_data,
            course_versions,
            date_modified=event_data.get("date_modified"),
            sf_term_data=current_term_data,
        )

        student_form_data = {
            "form_id": event_data.get("id"),
            "ccc_id": student_data.ccc_id,
            "enrollment_id": new_enrollment.id,
            "form_type": FormType.csep,
            "form_status": FormStatus.completed,
            "document_url": document_link,
            "form_metadata": {
                "form_service": "PandaDoc",
            },
        }
        update_or_create(self.calbright.session, StudentForm, student_form_data, form_id=event_data.get("id"))
        if extra_data.get("lms") == "Canvas":
            from propus.helpers.canvas import create_initial_course_enrollment

            create_initial_course_enrollment(
                ccc_id=student_data.ccc_id,
                session=self.calbright.session,
                canvas=self.canvas,
                orientation_course_section_id=self.orientation_section_id,
            )
            courses = set()
            for ect in new_enrollment.enrollment_enrollment_course_term:
                courses.add(ect.course_version.course.course_code)
                ect.instructor_id = ect.course_version_section.instructor_id
                self.salesforce.client.update_end_of_term_grade(
                    ect.grade_salesforce_id,
                    lookup_student=False,
                    Instructor__c=ect.course_version_section.instructor.user.salesforce_id,
                )

            sf_update_data = {f"Course_{idx+1}__c": c for idx, c in enumerate(sorted(courses))}
            self.salesforce.client.update_contact_record(student_data.user.salesforce_id, **sf_update_data)

        self.hubspot.send_transactional_email(
            email_id=self.csep_complete_email_id,
            to_email=student_data.user.calbright_email,
            email_name="CSEP_Complete",
            custom_properties={
                "enrollment_agreement": document_link,
                "academic_counselor": extra_data.get("cfg_Assigned_Learner_Advocate__r", {}).get("Name"),
                "intended_program": extra_data.get("intended_program"),
                "first_name": student_data.user.first_name,
            },
        )

        if pd_requests.get("veterans_services"):
            self.request_veteran_services(
                student_data, event_data.get("date_modified"), extra_data.get("Veteran_Service_Records__r")
            )

        if pd_requests.get("chromebook_requested") or pd_requests.get("hotspot_requested"):
            pd_shipping_address = self.get_shipping_address(event_data)
            tangoe_data = {
                "event_type": "tangoe_event",
                "event_data": {
                    "student_info": {
                        "first_name": student_data.user.first_name,
                        "last_name": student_data.user.last_name,
                        "phone": student_data.user.phone_number,
                        "email": student_data.user.calbright_email,
                        "id": student_data.user.salesforce_id,
                        "street": pd_shipping_address.get("street", ""),
                        "city": pd_shipping_address.get("city", ""),
                        "state": pd_shipping_address.get("state", ""),
                        "zipcode": pd_shipping_address.get("zipcode", ""),
                        "device_requested_method": "CSEP",
                        "device_agreement_sent_for_signature": extra_data.get(
                            "Device_Agreement_Sent_For_Signature_Date__c"
                        ),
                        "ccc_id": student_data.ccc_id,
                        "policy_signed": True,
                        "cb_requested": pd_requests.get("chromebook_requested"),
                        "hs_requested": pd_requests.get("hotspot_requested"),
                    },
                    "event_timestamp": self.datetime_now_isoformat,
                },
            }

            self.sqs.send_message(f'calbright_events_{os.environ.get("ENV")}', json.dumps(tangoe_data))
            self.logger.info(f"Created Device Request Event for: {student_data.user.calbright_email}.")

    def validate_csep_data(self, event_data: dict):
        """
        Validates the CSEP data received from an event.

        Args:
            self: The instance of the class containing this method.
            event_data (dict): A dictionary containing the event data, including tokens and fields.

        Returns:
            tuple: A tuple containing the following elements:
                - student (Student): An instance of the Student model representing the student.
                - sf_data (dict): A dictionary containing the student's Salesforce data, intended program, CRM status
                     and LMS information.

        Raises:
            CccIdNotInDatabase: If the student's CCC ID is not found in the database.
            Exception: If the program name doesn't match the intended program in Salesforce, or if a program tag ID is
                not found in Propus for a non-CRM program.
            CalbrightEmailNotInSalesforce: If the student's Calbright email is not found or doesn't match the email in
                Salesforce.
            MissingAcademicCounselor: If no academic support counselor is assigned to the student in Salesforce.

        This method performs the following steps:

        1. Extracts the tokens from the event data.
        2. Checks if the required fields are present in the tokens.
        3. Validates the student's Calbright email.
        4. Determines the program name and whether it is a CRM program.
        5. Retrieves the LMS information based on the program name.
        6. Fetches the student data from the database using the CCC ID.
        7. Retrieves the student's Salesforce data.
        8. Validates the program name against the intended program in Salesforce.
        9. Checks if the program tag ID exists in Propus for non-CRM programs.
        10. Validates the student's learner status against the valid learner status for the LMS.
        11. Checks if the student has an existing program enrollment in progress.
        12. Validates the student's Calbright email against the email in Salesforce.
        13. Checks if an academic support counselor is assigned to the student in Salesforce.
        14. Returns the student data and a dictionary containing the Salesforce data, intended program, CRM status, and
            LMS information.

        The method uses various attributes and methods from other classes to interact with the database, Salesforce,
            and other services.
        """
        tokens = {k: v for d in event_data.get("tokens") for k, v in d.items()}
        self.check_required_fields(self.__event_type__, tokens, self._required_tokens)

        validate_email(tokens.get("Student.CalbrightEmail"))

        program_name = PROGRAM_API_VALUE_MAP.get(tokens.get("Student.ProgramName"))

        crm = program_name == "T2T CRM Admin"
        if re.search(r"uatest\d{1}.demo@calbrightcollege.org", tokens.get("Student.CalbrightEmail")):
            self.override_canvas = True
        lms, db_lms = ["myTrailhead", LMS.trailhead] if crm else self.fetch_non_crm_lms(program_name)

        try:
            student = self.calbright.session.execute(
                select(Student).filter_by(ccc_id=tokens.get("Student.CCCID"))
            ).scalar_one()
        except NoResultFound:
            raise CccIdNotInDatabase(tokens.get("Student.CCCID"))

        sf_data = self.salesforce.get_student_salesforce_fields(tokens.get("Student.CCCID"))
        if not sf_data.get("cfg_Intended_Program__c") or program_name != sf_data.get("cfg_Intended_Program__c"):
            raise Exception(
                f"""{student.ccc_id}: Program name "{program_name}"
                doesn't match with intended program "{sf_data.get('cfg_Intended_Program__c')}" found on Salesforce."""
            )
        if not crm and not self.strut.program_tag_ids.get(program_name):
            raise Exception(f"A tag id for {program_name} wasn't found in Propus.")
        if not student.user.learner_status or student.user.learner_status.status not in VALID_LEARNER_STATUS[lms]:
            raise Exception(f"{student.ccc_id}: Invalid Learner Status for {program_name}.")
        if any([True for e in student.enrollment_student if e.enrollment_status.status in ["Enrolled", "Started"]]):
            raise Exception(f"{student.ccc_id}: Existing program enrollment for was found In Progress.")
        if not student.user.calbright_email or student.user.calbright_email != tokens.get("Student.CalbrightEmail"):
            raise CalbrightEmailNotInSalesforce(tokens.get("Student.CalbrightEmail"))

        asc_key = "cfg_Assigned_Learner_Advocate__r"
        if not sf_data.get(asc_key) or not sf_data.get(asc_key).get("Id"):
            self.logger.error(f"no academic support counselor assigned for {student.ccc_id}")
            raise MissingAcademicCounselor(student.ccc_id)
        try:
            asc_user = self.calbright.session.execute(
                select(User).filter_by(salesforce_id=sf_data.get(asc_key).get("Id"))
            ).scalar_one()
        except NoResultFound:
            raise MissingAcademicCounselorInDb(sf_data.get(asc_key).get("Id"))

        return student, sf_data | {
            "intended_program": program_name,
            "is_crm": crm,
            "lms": lms,
            "db_lms": db_lms,
            "asc_user": asc_user,
        }

    def create_enrollment_objects(
        self, student: Student, extra_data: dict, course_versions: list, date_modified: AnyStr, sf_term_data: dict
    ):
        """
        Creates enrollment objects for a student in Salesforce and the database.

        Args:
            student (Student): The student object for whom the enrollment objects are being created.
            extra_data (dict): A dictionary containing additional data required for enrollment creation.
            course_versions (list): A list of course versions for the program the student is enrolling in.
            date_modified (str): The date of enrollment.
            sf_term_data (dict): A dictionary containing Salesforce term data.

        Returns:
            int: The ID of the newly created enrollment in the database.

        Raises:
            SalesforceProgramEnrollmentError: If the Salesforce program enrollment record creation fails.
            InstructorNotInDatabase: If the instructor for a course is not found in the database.

        This function performs the following tasks:
        1. Creates a Salesforce program enrollment record for the student.
        2. Fetches the program version based on the course versions.
        3. Creates an enrollment record in the database.
        4. Fetches the courses for the program and creates a mapping of course codes to course objects.
        5. Removes courses that the student has already completed from the course code map.
        6. For each remaining course:
            a. Creates an end-of-term grade record in Salesforce.
            b. Fetches the instructor for the course from Salesforce and the corresponding user from the database.
            c. Creates an enrollment course term record in the database.
        7. Commits the changes to the database session.
        8. Returns the ID of the newly created enrollment.
        """
        # Create Salesforce Enrollment
        response = self.salesforce.client.create_program_enrollment_record(
            program_name=(
                extra_data.get("intended_program")
                if not extra_data.get("is_crm")
                else "Customer Relationship Management"
            ),
            contact=student.user.salesforce_id,
            date_of_enrollment=date_modified,
            enrollment_status="In Progress",
            program_version=str.join(", ", course_versions) if course_versions else None,
        )
        if not response.get("id"):
            raise SalesforceProgramEnrollmentError(student.ccc_id)

        db_program_short_name = (
            extra_data.get("intended_program")
            if extra_data.get("intended_program") != "T2T CRM Admin"
            else "Customer Relationship Management"
        )
        program_version = fetch_program_version_by_course_versions(
            self.calbright.session,
            db_program_short_name,
            program_version=str.join(", ", course_versions) if course_versions else None,
        )

        enrollment_data = {
            "enrollment_salesforce_id": response.get("id"),
            "program_version_id": program_version,
            "enrollment_status": self.calbright.session.execute(
                select(EnrollmentStatus).filter_by(status="Enrolled")
            ).scalar_one(),
            "enrollment_date": date_modified,
            "lms": extra_data.get("db_lms"),
            "student": student,
        }
        new_enrollment = upsert_enrollment(self.calbright.session, student.user, enrollment_data)
        self.calbright.session.flush()
        self.calbright.session.add(
            EnrollmentCounselor(
                enrollment_id=new_enrollment.id,
                counselor_id=extra_data.get("asc_user").staff_id,
                current_counselor=True,
            )
        )
        courses = fetch_courses_for_program(self.calbright.session, db_program_short_name, program_version)
        course_code_map = {c.course_code: c for c in courses}
        # Remove courses that student has already completed
        for enrollment in student.enrollment_student:
            for prev_course in enrollment.enrollment_enrollment_course_term:
                if prev_course.grade.grade == "P" and prev_course.course_version.course.course_code in course_code_map:
                    del course_code_map[prev_course.course_version.course.course_code]
        enrollment_course_term_records = []

        for course_code, course in course_code_map.items():
            response = self.salesforce.client.create_end_of_term_grade(
                course_code,
                student.ccc_id,
                student.user.salesforce_id,
                sf_term_data.get("Id"),
                sf_term_data.get("Name"),
            )
            salesforce_instructor = self.salesforce.client._fetch_instructor(course_code)
            instructor_user = self.calbright.session.execute(
                select(User).filter_by(salesforce_id=salesforce_instructor)
            ).scalar_one()
            if not instructor_user or not instructor_user.staff:
                raise InstructorNotInDatabase(salesforce_instructor)
            # Create Database Enrollment Course Term Objects
            ect_record = upsert_eotg_records(
                session=self.calbright.session,
                term_id=new_enrollment.first_term.id,
                sf_grade_id=response.get("id"),
                course=course,
                instructor_id=instructor_user.staff_id if extra_data.get("lms") != "Canvas" else None,
                enrollment=new_enrollment,
            )
            enrollment_course_term_records.append(ect_record[0])

        if extra_data.get("lms") == "Canvas":
            from propus.helpers.sql_calbright.enrollment import assign_enrollment_course_term_sections

            assign_enrollment_course_term_sections(self.calbright.session, enrollment_course_term_records, commit=False)

        self.calbright.session.commit()
        return new_enrollment

    def request_veteran_services(self, student_data: Student, date_completed: AnyStr, veteran_records: AnyStr = None):
        """
        Handles the process of requesting veteran services for a student.

        Args:
            student_data (Student Object): An SQLAlchemy Student Object record containing student data, including user
                information and ccc_id.
            date_completed (string): The date when the csep form was completed.
            veteran_records (string): The Salesforce ID of any previously created vet records

        This method performs the following actions:

        1. If `veteran_records` is None (no existing veteran record):
            - Creates a new veteran record in Salesforce with the `intake_form_sent` date set to `date_completed`.
            - Sends the veteran services intake form to the student's email using the HubSpot API.
                - Creates a Salesforce task to track the email sent to the student.

        2. If `veteran_records` is not None (existing veteran record):
            - Sends an email to the student with a link to continue veteran services using the HubSpot API.
                - Creates a Salesforce task to track the email sent to the student.
            - Sends an email to the veteran services team to follow up with the student using the HubSpot API.

        The method uses the `self.logger`, `self.salesforce.client`, `self.hubspot`, and `self.veteran_services_email`
        attributes to perform the necessary operations.
        """
        if veteran_records is None:
            self.logger.info(f"{student_data.ccc_id}: no veteran record found, continuing with event")
            #  Create a new Veteran Record in Salesforce (Add date completed for when Veteran intake form was sent)
            self.salesforce.client.create_vet_record(student_data.user.salesforce_id, intake_form_sent=date_completed)

            # Send them the intake form to fill out
            self.hubspot.send_transactional_email(
                email_id=self.veteran_services_intake_request_email_id,
                to_email=student_data.user.calbright_email,
                email_name="[PROD] VeteransServices: Send Intake Form",
                custom_properties={
                    "first_name": student_data.user.first_name,
                },
                salesforce_task={
                    "client": self.salesforce.client,
                    "task_data": {
                        "salesforce_id": student_data.user.salesforce_id,
                        "activity_date": self.datetime_now.strftime("%Y-%m-%d"),
                        "status": "Completed",
                        "subject": "Emailed Veteran Services Intake Form",
                        "description": "Veteran services intake form was sent to student through hubspot",
                        "type": "Email",
                    },
                },
            )
        else:
            self.logger.info(f"{student_data.ccc_id}: current veteran record found, continuing with event")
            #   Send them an email with an appointment link
            self.hubspot.send_transactional_email(
                email_id=CONTINUE_SERVICES_TO_STUDENT,
                email_name="VeteransServices: Continue Services",
                to_email=student_data.user.calbright_email,
                salesforce_task={
                    "client": self.salesforce.client,
                    "task_data": {
                        "salesforce_id": student_data.user.salesforce_id,
                        "activity_date": self.datetime_now.strftime("%Y-%m-%d"),
                        "status": "Completed",
                        "subject": "Emailed Veteran Services Continuation Email",
                        "description": "Emailed student the continuation email with veteran services email",
                        "type": "Email",
                    },
                },
            )

            # Send and email to VS so they can follow up
            self.hubspot.send_transactional_email(
                email_id=CONTINUE_SERVICES_TO_VS_TEAM,
                to_email=self.veteran_services_email,
                email_name="VeteransServices: Requested Services Continuation",
                custom_properties={
                    "first_name": student_data.user.first_name,
                    "last_name": student_data.user.last_name,
                    "ccc_id": student_data.ccc_id,
                },
            )

    def enroll_student_in_trailhead(self, student_data: Student, customer_community_user: AnyStr):
        """
        Enrolls a student in the Trailhead courses based on their assigned Trailmixes.

        Args:
            student_data (Student): An object containing student data, including user information and ccc_id.
            customer_community_user (AnyStr): A string indicating whether the student is a customer community user.

        Returns:
            list: A list of course versions the student is enrolled in.
        """
        course_versions = []
        if customer_community_user:
            trailmix_assignments = self.salesforce.get_trailmix_assignments(student_data.user.salesforce_id)
            for trailmix in trailmix_assignments:
                trailmix_code = trailmix.get("trailheadapp__Trailmix__c")
                course_versions.append(COURSE_CODES_TABLE.get(trailmix_code))

            self.salesforce.client.update_contact_record(
                student_data.user.salesforce_id,
                cfg_Learner_Status__c="Enrolled in Program Pathway",
                Program_Version__c=str.join(", ", course_versions),
            )
            student_data.user.learner_status = self.calbright.session.execute(
                select(LearnerStatus).filter_by(status="Enrolled in Program Pathway")
            ).scalar_one()
            self.calbright.session.commit()
        self.logger.info(f"{student_data.ccc_id}: myTrailhead enrolled")
        return course_versions

    def enroll_student_in_strut(self, student_data: Student, intended_program: AnyStr, coach_id: AnyStr):
        """
        Enrolls a student in the Strut Learning Management System (LMS) for a given program.

        Args:
            student_data (Student): An object containing student data, including user information, ccc_id, and
                enrollment details.
            intended_program (AnyStr): A string representing the program the student is enrolling in.
            coach_id (AnyStr): A string representing the ID of the coach assigned to the student.

        This method performs the following steps:

        1. Retrieves the student's Strut LMS ID from the `user_lms` list in the `student_data` object.

        2. If the student has a Strut LMS ID:
            a. Fetches the student's existing tags in Strut using the `self.strut.fetch_student_tags` method.
            b. Removes all existing tags from the student using the `self.strut.remove_all_student_tags` method.
            c. Assigns the new program tags to the student using the `self.strut.assign_student_tags` method.
            d. Sets the student's state to "active" in Strut using the `self.strut.assign_student_state` method.
            e. Retrieves the student's previously completed courses and grades.
            f. Enrolls the student in the pathway competencies for the intended program using the
                `self.enroll_student_in_pathway_competencies` method, considering the completion of the WF500 course.
            g. Updates the student's status in a Google Sheet using the `self.gsheets.adjust_ou_to_enrolled_student`
                method.

        3. If the student does not have a Strut LMS ID:
            a. Enqueues the student for Strut enrollment using the `self.gsheets.enqueue_student_to_strut` method,
                providing the student's information and the intended program.

        4. Logs a message indicating that the student with the given `ccc_id` has been enrolled in the intended
            program in Strut.

        The method uses the `self.strut`, `self.gsheets`, and `self.logger` attributes to interact with the Strut LMS,
            Google Sheets, and logging, respectively.
        """
        student_strut_id = None
        for lms in student_data.user.user_lms:
            if lms.lms == LMS.strut:
                student_strut_id = lms.lms_id
                break

        if student_strut_id:
            student_tags = self.strut.fetch_student_tags(student_strut_id)
            if student_tags:
                self.strut.remove_all_student_tags(student_strut_id, {tag.get("id") for tag in student_tags})
            self.strut.assign_student_tags(student_strut_id, intended_program)
            self.strut.assign_student_state(student_strut_id, "active")

            previous_courses = [
                [ect.course_version.course.course_code, ect.grade.grade]
                for e in student_data.enrollment_student
                for ect in e.enrollment_enrollment_course_term
                if ect.grade and ect.grade.grade == "P" and ect.course_version.course.course_code
            ]
            self.enroll_student_in_pathway_competencies(
                strut_id=student_strut_id,
                program_name=intended_program,
                completed_wf500=["WF500", "P"] in previous_courses,
            )
            self.gsheets.adjust_ou_to_enrolled_student(
                time=self.datetime_now_isoformat,
                first_name=student_data.user.first_name,
                last_name=student_data.user.last_name,
                email=student_data.user.calbright_email,
                status="",
                message="",
            )
        else:
            self.gsheets.enqueue_student_to_strut(
                username=student_data.user.calbright_email.split("@")[0],
                first_name=student_data.user.first_name,
                last_name=student_data.user.last_name,
                email=student_data.user.calbright_email,
                role="student",
                coach_id=coach_id,
                state="",
                strut_id="",
                intended_program=self.strut.program_tag_ids.get(intended_program),
            )
        self.logger.info(f"{student_data.ccc_id}: Strut Enrolled into: {intended_program}")

    def enroll_student_in_pathway_competencies(self, strut_id, program_name, completed_wf500=False, record_count=100):
        """Grab current enrollments for a student and activate the competencies tied to the program. If there aren't
        any competencies locked, create new competencies tied to the student or perform a product purchase for specific
        programs.

        Args:
            student (dict): Student dictionary returned from Salesforce
            record_count (int, optional): The amount of records that will appear on enrollment query. This can be a
                large number depending on amount of programs enrolled in. Defaults to 100.
        """

        student_competencies_ids = STRUT_COMPETENCY_IDS.get(program_name)
        student_product_ids = PROGRAM_PRODUCT_IDS.get(program_name)
        existing_completion_competencies_ids = EXISTING_COMPETENCY_IDS_CHECK.get(program_name)
        existing_completion_product_ids = EXISTING_COMPLETION_PRODUCT_IDS.get(program_name)

        enable_existing_product_id = False

        if not completed_wf500 and program_name in ("IT Support", "Cybersecurity"):
            student_competencies_ids.append(210)

        enrollments = self.strut.fetch_enrollments(student_id=strut_id, shallow=True, count=record_count)

        for enrollment in enrollments:
            if enrollment.get("competency").get("id") in student_competencies_ids:
                if enrollment.get("state") == "locked":
                    # Activate the enrollment from locked state
                    self.strut.update_enrollment(student_strut_id=strut_id, enrollment_id=enrollment.get("id"))
                student_competencies_ids.remove(enrollment.get("competency").get("id"))
            if (
                program_name in ("Data Analysis")
                and enrollment.get("competency").get("id") in existing_completion_competencies_ids
            ):
                enable_existing_product_id = True

        if program_name in ("Data Analysis", "T2T Intro to Networks", "Project Management"):
            assigned_products = self.strut.fetch_product_ids(strut_id)
            assigned_product_ids = []
            for product in assigned_products.get("product_purchases"):
                assigned_product_ids.append(product.get("product").get("id"))

            # Need either the existing competency product ids or the standard product ids then remove existing ids
            product_ids = list(
                set(existing_completion_product_ids if enable_existing_product_id else student_product_ids).difference(
                    assigned_product_ids
                )
            )

            for product_id in product_ids:
                self.strut.add_product_to_student(strut_id, product_id)
        else:
            for competency_id in student_competencies_ids:
                self.strut.create_enrollment(student_strut_id=strut_id, competency_id=competency_id)

    # Helper Functions below here
    def fetch_non_crm_lms(self, prog_name: AnyStr) -> tuple[AnyStr, LMS]:
        """
        Determines the Learning Management System (LMS) to use for a given program.

        Args:
            prog_name (str): The name of the program.

        Returns:
            tuple: A tuple containing the name of the LMS as a string and the corresponding LMS enum value.
                If the program has a Canvas launch date and the current date is after that launch date,
                it returns "Canvas" and the LMS.canvas enum value.
                Otherwise, it returns "Strut" and the LMS.strut enum value.
        """
        canvas_launch_date = CANVAS_LAUNCH_DATES_BY_PROGRAM.get(prog_name)
        if canvas_launch_date and (self.datetime_now.replace(tzinfo=None) > canvas_launch_date or self.override_canvas):
            self.logger.info(f"Using Canvas for {prog_name}")
            return "Canvas", LMS.canvas
        return "Strut", LMS.strut

    @staticmethod
    def get_csep_requests(event_data: Dict) -> Dict:
        """
        Get the CSEP requests from the event data.
        :param event_data: The event data.
        :return: A dictionary of the CSEP requests.
        """
        fields = {field.get("field_id"): field for field in event_data.get("fields")}

        requests = {}
        for key, panda_key in {
            "chromebook_requested": "Chromebook_Requested",
            "hotspot_requested": "HotSpot_Requested",
            "accessibility_services": "Accessibility_Services",
            "veterans_services": "Veterans_Services",
        }.items():
            requests[key] = (
                "Yes" in fields.get(panda_key, {}).get("value") if fields.get(panda_key, {}).get("value") else False
            )
        return requests

    @staticmethod
    def get_shipping_address(event_data: Dict) -> Dict:
        """
        Get the shipping address from the event data.
        :param event_data: The event data.
        :return: A dictionary of the shipping address.
        """
        fields = {field.get("field_id"): field for field in event_data.get("fields")}

        requests = {}
        for key, panda_key in {
            "street": "StreetAddress",
            "city": "City",
            "state": "State",
            "zipcode": "ZipCode",
        }.items():
            requests[key] = fields.get(panda_key, {}).get("value")
        return requests
