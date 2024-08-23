from datetime import datetime, timedelta
from sqlalchemy.exc import NoResultFound
import unittest
from unittest.mock import MagicMock, Mock, patch

from propus.calbright_sql.course import Course
from propus.calbright_sql.course_version import CourseVersion
from propus.calbright_sql.enrollment import Enrollment, LMS
from propus.calbright_sql.enrollment_course_term import EnrollmentCourseTerm
from propus.calbright_sql.enrollment_status import EnrollmentStatus
from propus.calbright_sql.grade import Grade
from propus.calbright_sql.learner_status import LearnerStatus
from propus.calbright_sql.student import Student
from propus.calbright_sql.staff import Staff
from propus.calbright_sql.term import Term
from propus.calbright_sql.user import User
from propus.calbright_sql.user_lms import UserLms
from propus.helpers.exceptions import InvalidEmail


from exceptions import MissingRequiredField, CalbrightEmailNotInSalesforce
from events.constants import CANVAS_LAUNCH_DATES_BY_PROGRAM
from events.csep_complete import (
    CsepComplete,
    SalesforceProgramEnrollmentError,
    InstructorNotInDatabase,
)


class TestEventCsepComplete(unittest.TestCase):

    def setUp(self):
        self.salesforce = MagicMock()
        self.salesforce.client.create_vet_record = Mock(side_effect=self.create_vet_record)
        self.salesforce.client.create_program_enrollment_record = Mock(side_effect=self.create_program_enrollment)
        self.salesforce.client.create_end_of_term_grade = Mock(side_effect=self.create_end_of_term_grade)
        self.salesforce.get_trailmix_assignments = Mock(side_effect=self.get_trailmix_assingments)
        self.salesforce.get_student_salesforce_fields = Mock(side_effect=self.get_student_salesforce_fields)
        self.salesforce.client.update_contact_record = Mock(side_effect=self.update_contact_record)

        hubspot = MagicMock()
        hubspot.send_transactional_email = Mock(side_effect=self.send_transactional_email)

        slack = MagicMock()
        slack.alert_student_signed_csep = Mock(side_effect=self.alert_student_signed_csep)

        gsheet = MagicMock()
        gsheet.enqueue_student_to_strut = Mock(side_effect=self.enqueue_student_to_strut)
        gsheet.adjust_ou_to_enrolled_student = Mock(side_effect=self.adjust_ou_to_enrolled_student)

        strut = MagicMock()
        self.it_support_id = "it_support_12345"
        strut.program_tag_ids = {"IT Support": self.it_support_id}
        strut.fetch_student_tags = Mock(side_effect=self.fetch_student_tags)
        strut.remove_all_student_tags = Mock(side_effect=self.remove_all_student_tags)
        strut.assign_student_tags = Mock(side_effect=self.assign_student_tags)
        strut.assign_student_state = Mock(side_effect=self.assign_student_state)
        strut.fetch_enrollments = Mock(side_effect=self.fetch_enrollments)
        strut.update_enrollment = Mock(side_effect=self.update_enrollment)
        strut.create_enrollment = Mock(side_effect=self.create_enrollment)
        strut.fetch_product_ids = Mock(side_effect=self.fetch_product_ids)
        strut.add_product_to_student = Mock(side_effect=self.add_product_to_student)

        session = MagicMock()
        session.execute = Mock(side_effect=self.session_execute)
        session.flush.return_value = True

        self.calbright = MagicMock()
        self.calbright.session = session

        self.sqs = MagicMock()
        self.sqs.send_message.return_value = True

        self.veteran_services_email = "vs@cal.org"
        self.vet_intake_email_id = 9613426781234
        self.csep_complete_email_id = 145977075626

        canvas = MagicMock()

        self.csep_complete = CsepComplete(
            configs={
                "constants": {"email": {"veterans": self.veteran_services_email}},
                "csep_complete": {
                    "veteran_services_intake_request_id": self.vet_intake_email_id,
                    "csep_complete_email_id": self.csep_complete_email_id,
                },
            },
            salesforce=self.salesforce,
            hubspot=hubspot,
            gsheets=gsheet,
            slack=slack,
            strut=strut,
            sqs=self.sqs,
            calbright=self.calbright,
            canvas=canvas,
        )

        self.asc_user = User(staff_id="ASC_1235")

        self.test_event_data = {
            "csep_complete_date": "Date The CSEP was Completed",
            "instructor": User(staff_id="INSTRUCTOR_1234", staff=Staff(id="INSTRUCTOR_1234")),
            "student": Student(
                ccc_id="AUD2286",
                user=User(
                    salesforce_id="ABC_1234_YXZ",
                    first_name="Johnnie",
                    last_name="Appleseed",
                    personal_email="personal_email@gmail.com",
                    calbright_email="johnnie.appleseed@calbrightcollege.org",
                    user_lms=[],
                ),
                enrollment_student=[
                    Enrollment(
                        enrollment_enrollment_course_term=[
                            EnrollmentCourseTerm(
                                grade=Grade(grade="P"), course_version=CourseVersion(course=Course(course_code="WF500"))
                            )
                        ]
                    )
                ],
            ),
            "veteran_services_id": "VET_1234_XYZ",
            "intended_program": "IT Support",
            "coach_id": "COACH_1234_9876",
            "strut_uname": "johnnie.appleseed",
            "strut_tags": [{"id": 142}, {"id": 1112}, {"id": 324}],
            "strut_enrollment": UserLms(lms=LMS.strut, lms_id=837420),
            "strut_competency_id": "HGSK7891230",
            "program_version_id": "IT_500_1234",
            "courses": [
                Course(
                    course_name="Introduction to Data Analysis",
                    course_code="WF500",
                ),
                Course(
                    course_name="Data Analysis with Python",
                    course_code="IT500",
                ),
            ],
            "course_versions": ["IT500 V1", "WF500 V2"],
            "date_modified": "2024-06-17T03:23:45",
            "sf_term_data": {"Id": "0023SDHJ21389", "Name": "2023-24-TERM-05"},
            "sf_enrollment_id": "enroll_id_678213",
            "enrollment_status": EnrollmentStatus(id="123456459", status="Enrolled"),
            "sf_eotg_grade_resp": {"id": "GRADE_123_987"},
            "first_term_id": "TERM_ID_12345",
            "new_enrollment": Enrollment(
                id="DB_UUID_12378",
                first_term=Term(id="TERM_ID_12345"),
            ),
            "accessibility_services": True,
            "is_crm": True,
            "recipients": [{"shared_link": "HTTPS://LINK.ME"}],
            "learner_status": LearnerStatus(status="Completed CSEP"),
        }

        self.salesforce.get_next_term.return_value = {"Id": self.test_event_data.get("first_term_id")}

    @patch("events.csep_complete.update_or_create")
    def test_run(self, mock_update_or_create):
        validate_csep_mock = MagicMock()
        validate_csep_mock.return_value = [
            self.test_event_data.get("student"),
            {
                "intended_program": self.test_event_data.get("intended_program"),
                "is_crm": self.test_event_data.get("is_crm"),
                "lms": "Strut",
                "cfg_Assigned_Learner_Advocate__r": {"Strut_User_ID__c": "ABC_1234"},
            },
        ]
        self.csep_complete.validate_csep_data = validate_csep_mock

        get_csep_reqs_mock = MagicMock()
        get_csep_reqs_mock.return_value = {
            "veterans_services": True,
            "accessibility_services": self.test_event_data.get("accessibility_services"),
            "chromebook_requested": True,
        }
        self.csep_complete.get_csep_requests = get_csep_reqs_mock

        enroll_student_in_strut = MagicMock()
        enroll_student_in_strut.return_value = True
        self.csep_complete.enroll_student_in_strut = enroll_student_in_strut
        request_veteran_services = MagicMock()
        request_veteran_services.return_value = True
        self.csep_complete.request_veteran_services = request_veteran_services

        create_enrollment_objects_mock = MagicMock()
        create_enrollment_objects_mock.return_value = self.test_event_data.get("new_enrollment")
        self.csep_complete.create_enrollment_objects = create_enrollment_objects_mock

        get_shipping_address_mock = MagicMock()
        get_shipping_address_mock.return_value = {}
        self.csep_complete.get_shipping_address = get_shipping_address_mock

        self.slack_assigned_csep = False
        self.update_contact_record = False
        self.hubspot_called = False
        self.test_name = "TestRun"
        self.csep_complete.run(
            event_data={
                "date_modified": self.test_event_data.get("date_modified"),
                "recipients": self.test_event_data.get("recipients"),
                "lms": "Canvas",
            }
        )
        self.assertTrue(all([self.slack_assigned_csep, self.update_contact_record, self.hubspot_called]))
        self.csep_complete.enroll_student_in_strut.assert_called_once_with(
            self.test_event_data.get("student"), self.test_event_data.get("intended_program"), "ABC_1234"
        )
        mock_update_or_create.assert_called_once()
        request_veteran_services.assert_called_once()
        get_shipping_address_mock.assert_called_once()
        self.sqs.send_message.assert_called_once()

    @patch("events.csep_complete.upsert_eotg_records")
    @patch("events.csep_complete.fetch_courses_for_program")
    @patch("events.csep_complete.upsert_enrollment")
    @patch("events.csep_complete.fetch_program_version_by_course_versions")
    def test_create_enrollment_objects(
        self,
        mock_fetch_program_version,
        mock_upsert_enrollment,
        mock_fetch_courses_for_program,
        mock_upsert_eotg,
    ):
        mock_fetch_courses_for_program.return_value = self.test_event_data.get("courses")
        mock_fetch_program_version.return_value = self.test_event_data.get("program_version_id")
        mock_upsert_enrollment.return_value = self.test_event_data.get("new_enrollment")

        self.test_name = "SfEnrollmentError"
        with self.assertRaises(SalesforceProgramEnrollmentError) as err:
            self.csep_complete.create_enrollment_objects(
                student=self.test_event_data.get("student"),
                extra_data={
                    "intended_program": self.test_event_data.get("intended_program"),
                    "asc_user": self.asc_user,
                },
                course_versions=self.test_event_data.get("course_versions"),
                date_modified=self.test_event_data.get("date_modified"),
                sf_term_data=self.test_event_data.get("sf_term_data"),
            )
        self.assertEqual(str(err.exception), "Failed to create salesforce program enrollment for AUD2286")

        self.test_name = "EnrollmentTest"
        enrollment_response = self.csep_complete.create_enrollment_objects(
            student=self.test_event_data.get("student"),
            extra_data={
                "intended_program": self.test_event_data.get("intended_program"),
                "asc_user": self.asc_user,
            },
            course_versions=self.test_event_data.get("course_versions"),
            date_modified=self.test_event_data.get("date_modified"),
            sf_term_data=self.test_event_data.get("sf_term_data"),
        )
        self.assertEqual(enrollment_response, self.test_event_data.get("new_enrollment"))
        mock_fetch_program_version.assert_called_once_with(
            self.calbright.session, self.test_event_data.get("intended_program"), program_version="IT500 V1, WF500 V2"
        )
        mock_upsert_enrollment.assert_called_once_with(
            self.calbright.session,
            self.test_event_data.get("student").user,
            {
                "enrollment_salesforce_id": "enroll_id_678213",
                "program_version_id": "IT_500_1234",
                "enrollment_status": self.test_event_data.get("enrollment_status"),
                "enrollment_date": "2024-06-17T03:23:45",
                "lms": None,
                "student": self.test_event_data.get("student"),
            },
        )
        mock_fetch_courses_for_program.assert_called_once_with(
            self.calbright.session,
            self.test_event_data.get("intended_program"),
            self.test_event_data.get("program_version_id"),
        )

        mock_upsert_eotg.assert_called_once_with(
            session=self.calbright.session,
            term_id=self.test_event_data.get("first_term_id"),
            sf_grade_id=self.test_event_data.get("sf_eotg_grade_resp").get("id"),
            course=self.test_event_data.get("courses")[1],
            instructor_id=self.test_event_data.get("instructor").staff_id,
            enrollment=self.test_event_data.get("new_enrollment"),
        )

        self.test_name = "MissingInstructor"
        with self.assertRaises(InstructorNotInDatabase) as err:
            enrollment_response = self.csep_complete.create_enrollment_objects(
                student=self.test_event_data.get("student"),
                extra_data={
                    "intended_program": self.test_event_data.get("intended_program"),
                    "asc_user": self.asc_user,
                },
                course_versions=self.test_event_data.get("course_versions"),
                date_modified=self.test_event_data.get("date_modified"),
                sf_term_data=self.test_event_data.get("sf_term_data"),
            )
        self.assertTrue("Salesforce Instructor" in str(err.exception) and "not found in database" in str(err.exception))

    def test_validate_csep_data(self):
        self.test_event_data["intended_program"] = "Data Analysis"
        with self.assertRaises(MissingRequiredField):
            self.csep_complete.validate_csep_data({"tokens": {}})

        with self.assertRaises(MissingRequiredField):
            self.csep_complete.validate_csep_data(
                {"tokens": [{"Student.CCCID": self.test_event_data.get("student").ccc_id}]}
            )

        with self.assertRaises(MissingRequiredField):
            self.csep_complete.validate_csep_data(
                {
                    "tokens": [
                        {"Student.CCCID": self.test_event_data.get("student").ccc_id},
                        {"Student.CalbrightEmail": self.test_event_data.get("student").user.calbright_email},
                    ]
                }
            )

        with self.assertRaises(MissingRequiredField):
            self.csep_complete.validate_csep_data(
                {
                    "tokens": [
                        {"Student.CCCID": self.test_event_data.get("student").ccc_id},
                        {"Student.ProgramName": self.test_event_data.get("intended_program")},
                    ]
                }
            )

        with self.assertRaises(InvalidEmail):
            self.csep_complete.validate_csep_data(
                {
                    "tokens": [
                        {"Student.CCCID": self.test_event_data.get("student").ccc_id},
                        {"Student.CalbrightEmail": "This is an incalid email"},
                        {"Student.ProgramName": self.test_event_data.get("intended_program")},
                    ]
                }
            )

        valid_tokens = [
            {"Student.CCCID": self.test_event_data.get("student").ccc_id},
            {"Student.CalbrightEmail": self.test_event_data.get("student").user.calbright_email},
            {"Student.ProgramName": "Introduction to Data Analysis"},
        ]

        self.test_name = "NoResultsFound"
        exception_raised = False
        try:
            self.csep_complete.validate_csep_data({"tokens": valid_tokens})
        except Exception as err:
            exception_raised = True
            self.assertIn("CCC ID AUD2286 was not found in database", str(err))

        self.assertTrue(exception_raised)

        self.test_name = "InvalidProgram"
        with self.assertRaises(Exception) as err:
            self.csep_complete.validate_csep_data({"tokens": valid_tokens})
        self.assertIn('AUD2286: Program name "Data Analysis"', str(err.exception))

        self.test_name = "MissingTags"
        with self.assertRaises(Exception) as err:
            self.csep_complete.validate_csep_data({"tokens": valid_tokens})
        self.assertEqual(str(err.exception), "A tag id for Data Analysis wasn't found in Propus.")

        valid_tokens[2]["Student.ProgramName"] = "IT Support"
        self.test_event_data["intended_program"] = "IT Support"
        with self.assertRaises(Exception) as err:
            self.csep_complete.validate_csep_data({"tokens": valid_tokens})
        self.assertEqual(str(err.exception), "AUD2286: Invalid Learner Status for IT Support.")

        self.test_event_data.get("student").user.learner_status = LearnerStatus(status="Completed CSEP")
        self.test_event_data.get("student").enrollment_student = [
            Enrollment(enrollment_status=EnrollmentStatus(status="Enrolled"))
        ]
        with self.assertRaises(Exception) as err:
            self.csep_complete.validate_csep_data({"tokens": valid_tokens})
        self.assertEqual(str(err.exception), "AUD2286: Existing program enrollment for was found In Progress.")

        self.test_event_data.get("student").enrollment_student = []
        valid_tokens[1]["Student.CalbrightEmail"] = "john.doe@gmail.com"
        with self.assertRaises(CalbrightEmailNotInSalesforce):
            self.csep_complete.validate_csep_data({"tokens": valid_tokens})

        valid_tokens[1]["Student.CalbrightEmail"] = self.test_event_data.get("student").user.calbright_email
        asc_failed = False
        try:
            self.csep_complete.validate_csep_data({"tokens": valid_tokens})
        except Exception as err:
            asc_failed = True
            self.assertEqual(str(err), "No ASC is assigned for AUD2286")
        self.assertTrue(asc_failed)

        self.test_name = "successful_validation"
        student, sf_data = self.csep_complete.validate_csep_data({"tokens": valid_tokens})
        self.assertEqual(student, self.test_event_data.get("student"))
        expected_resp = {
            "cfg_Intended_Program__c": "IT Support",
            "cfg_Assigned_Learner_Advocate__r": {"Id": "ASC_1234"},
            "intended_program": "IT Support",
            "is_crm": False,
            "lms": "Strut",
            "db_lms": LMS.strut,
        }
        for key, value in expected_resp.items():
            self.assertEqual(sf_data.get(key), value)

    def test_fetch_non_crm_lms(self):
        canvas_program = list(CANVAS_LAUNCH_DATES_BY_PROGRAM.keys())[0]
        canvas_launch_date = CANVAS_LAUNCH_DATES_BY_PROGRAM.get(canvas_program)

        # Test a Canvas Launch Program
        self.csep_complete.datetime_now = canvas_launch_date + timedelta(days=1)
        self.assertEqual(
            self.csep_complete.fetch_non_crm_lms(prog_name=canvas_program),
            ("Canvas", LMS.canvas),
        )

        # Test a Canvas Launch Program before launch
        self.csep_complete.datetime_now = canvas_launch_date - timedelta(days=1)
        self.assertEqual(
            self.csep_complete.fetch_non_crm_lms(prog_name=canvas_program),
            ("Strut", LMS.strut),
        )

        # Test a Canvas Launch Program before launch
        self.csep_complete.datetime_now = datetime.now()
        self.assertEqual(
            self.csep_complete.fetch_non_crm_lms(prog_name="Strut Program"),
            ("Strut", LMS.strut),
        )

    def test_request_veteran_services(self):
        self.vet_record_created = False
        self.hubspot_called = False
        self.test_name = "NoVetServicesRecord"
        self.csep_complete.request_veteran_services(
            student_data=self.test_event_data.get("student"),
            date_completed=self.test_event_data.get("csep_complete_date"),
            veteran_records=None,
        )
        self.assertTrue(self.vet_record_created and self.hubspot_called)

        self.vet_record_created = False
        self.hubspot_called = False
        self.test_name = "VetServicesRecordFound"
        self.csep_complete.request_veteran_services(
            student_data=self.test_event_data.get("student"),
            date_completed=self.test_event_data.get("csep_complete_date"),
            veteran_records=self.test_event_data.get("veteran_services_id"),
        )
        self.assertTrue(not self.vet_record_created and self.hubspot_called)

    def test_enroll_student_in_strut(self):
        self.gsheets_updated = False
        self.csep_complete.enroll_student_in_strut(
            student_data=self.test_event_data.get("student"),
            intended_program=self.test_event_data.get("intended_program"),
            coach_id=self.test_event_data.get("coach_id"),
        )
        self.assertTrue(self.gsheets_updated)

        self.tests_to_pass = {}
        self.test_event_data.get("student").user.user_lms = [self.test_event_data.get("strut_enrollment")]
        self.csep_complete.enroll_student_in_strut(
            student_data=self.test_event_data.get("student"),
            intended_program=self.test_event_data.get("intended_program"),
            coach_id=self.test_event_data.get("coach_id"),
        )
        self.assertTrue(all(self.tests_to_pass.values()) and len(self.tests_to_pass) == 6)

        self.tests_to_pass = {}
        self.test_event_data["intended_program"] = "Data Analysis"
        self.csep_complete.enroll_student_in_strut(
            student_data=self.test_event_data.get("student"),
            intended_program=self.test_event_data.get("intended_program"),
            coach_id=self.test_event_data.get("coach_id"),
        )
        self.assertTrue(all(self.tests_to_pass.values()) and len(self.tests_to_pass) == 7)

    def test_enroll_student_in_trailhead(self):
        self.test_name = "EnrollInTrailhead"
        self.update_contact_record = False
        self.assertEqual(
            self.csep_complete.enroll_student_in_trailhead(
                student_data=self.test_event_data.get("student"),
                customer_community_user=True,
            ),
            ["IT520 - v1.0", "IT520 - v3.0"],
        )
        self.assertTrue(self.update_contact_record)

        self.assertListEqual(
            self.csep_complete.enroll_student_in_trailhead(
                student_data=self.test_event_data.get("student"),
                customer_community_user=False,
            ),
            [],
        )

    def test_get_csep_requests(self):
        # Arrange
        event_data = {
            "fields": [
                {"field_id": "Chromebook_Requested", "value": "Yes"},
                {"field_id": "HotSpot_Requested", "value": "Yes"},
                {"field_id": "Accessibility_Services", "value": "Yes"},
                {"field_id": "Veterans_Services", "value": "Yes"},
            ]
        }
        expected_output = {
            "chromebook_requested": True,
            "hotspot_requested": True,
            "accessibility_services": True,
            "veterans_services": True,
        }
        self.assertEqual(self.csep_complete.get_csep_requests(event_data), expected_output)

        event_data = {
            "fields": [
                {"field_id": "Chromebook_Requested", "value": "No"},
                {"field_id": "HotSpot_Requested", "value": "No"},
                {"field_id": "Accessibility_Services", "value": "No"},
                {"field_id": "Veterans_Services", "value": "No"},
            ]
        }
        expected_output = {
            "chromebook_requested": False,
            "hotspot_requested": False,
            "accessibility_services": False,
            "veterans_services": False,
        }
        self.assertEqual(self.csep_complete.get_csep_requests(event_data), expected_output)

        event_data = {"fields": []}
        expected_output = {
            "chromebook_requested": False,
            "hotspot_requested": False,
            "accessibility_services": False,
            "veterans_services": False,
        }
        self.assertEqual(self.csep_complete.get_csep_requests(event_data), expected_output)

    def test_get_shipping_address(self):
        event_data = {
            "fields": [
                {"field_id": "StreetAddress", "value": "123 Main St"},
                {"field_id": "City", "value": "Anytown"},
                {"field_id": "State", "value": "CA"},
                {"field_id": "ZipCode", "value": "12345"},
            ]
        }
        expected_output = {"street": "123 Main St", "city": "Anytown", "state": "CA", "zipcode": "12345"}
        self.assertEqual(self.csep_complete.get_shipping_address(event_data), expected_output)

        # Arrange
        event_data = {
            "fields": [
                {"field_id": "StreetAddress", "value": "123 Main St"},
                {"field_id": "City", "value": "Anytown"},
                {"field_id": "State", "value": ""},
                {"field_id": "ZipCode", "value": None},
            ]
        }
        expected_output = {"street": "123 Main St", "city": "Anytown", "state": "", "zipcode": None}
        self.assertEqual(self.csep_complete.get_shipping_address(event_data), expected_output)

        # Arrange
        event_data = {"fields": []}
        expected_output = {"street": None, "city": None, "state": None, "zipcode": None}

        self.assertEqual(self.csep_complete.get_shipping_address(event_data), expected_output)

    # test mock functions below here
    def send_transactional_email(self, *args, **kwargs):
        expected_kwargs = {
            "NoVetServicesRecord": {
                "email_id": 9613426781234,
                "to_email": "johnnie.appleseed@calbrightcollege.org",
                "email_name": "[PROD] VeteransServices: Send Intake Form",
                "custom_properties": {"first_name": "Johnnie"},
                "salesforce_task": {
                    "client": self.salesforce.client,
                    "task_data": {
                        "salesforce_id": "ABC_1234_YXZ",
                        "status": "Completed",
                        "subject": "Emailed Veteran Services Intake Form",
                        "description": "Veteran services intake form was sent to student through hubspot",
                        "type": "Email",
                    },
                },
            },
            "VetServicesRecordFound": {
                "email_id": 132545167026,
                "email_name": "VeteransServices: Continue Services",
                "to_email": "johnnie.appleseed@calbrightcollege.org",
                "salesforce_task": {
                    "client": self.salesforce.client,
                    "task_data": {
                        "salesforce_id": "ABC_1234_YXZ",
                        "status": "Completed",
                        "subject": "Emailed Veteran Services Continuation Email",
                        "description": "Emailed student the continuation email with veteran services email",
                        "type": "Email",
                    },
                },
            },
            "VetServicesRecordFound1": {
                "email_id": 115664761201,
                "to_email": None,
                "email_name": "VeteransServices: Requested Services Continuation",
                "custom_properties": {"first_name": "Johnnie", "last_name": "Appleseed", "ccc_id": "AUD2286"},
            },
            "TestRun": {
                "email_id": 145977075626,
                "to_email": "johnnie.appleseed@calbrightcollege.org",
                "email_name": "CSEP_Complete",
                "custom_properties": {
                    "enrollment_agreement": "HTTPS://LINK.ME",
                    "academic_counselor": None,
                    "intended_program": "IT Support",
                    "first_name": "Johnnie",
                },
            },
        }

        self.hubspot_called = True
        if expected_kwargs.get(self.test_name):
            if self.test_name in ["NoVetServicesRecord", "VetServicesRecordFound"]:
                del kwargs["salesforce_task"]["task_data"]["activity_date"]
            self.assertDictEqual(kwargs, expected_kwargs.get(self.test_name))

        self.test_name += "1"

    def create_vet_record(self, salesforce_id, intake_form_sent):
        self.assertEqual(salesforce_id, self.test_event_data.get("student").user.salesforce_id)
        self.assertEqual(intake_form_sent, self.test_event_data.get("csep_complete_date"))
        self.vet_record_created = True

    def get_trailmix_assingments(self, salesforce_id):
        self.assertEqual(salesforce_id, self.test_event_data.get("student").user.salesforce_id)
        return [
            {"trailheadapp__Trailmix__c": "a1m5G000005ss4DQAQ"},
            {"trailheadapp__Trailmix__c": "a1m5G000008uTo5QAE"},
        ]

    def enqueue_student_to_strut(self, **kwargs):
        self.assertEqual(kwargs.get("username"), self.test_event_data.get("strut_uname"))
        self.assertEqual(kwargs.get("first_name"), self.test_event_data.get("student").user.first_name)
        self.assertEqual(kwargs.get("last_name"), self.test_event_data.get("student").user.last_name)
        self.assertEqual(kwargs.get("email"), self.test_event_data.get("student").user.calbright_email)
        self.assertEqual(kwargs.get("intended_program"), self.it_support_id)
        self.assertEqual(kwargs.get("coach_id"), self.test_event_data.get("coach_id"))
        self.assertEqual(kwargs.get("role"), "student")
        self.assertEqual(kwargs.get("state"), "")
        self.assertEqual(kwargs.get("strut_id"), "")
        self.gsheets_updated = True

    def adjust_ou_to_enrolled_student(self, **kwargs):
        self.gsheet_adjust_ou_enrolled = True
        self.assertEqual(kwargs.get("first_name"), "Johnnie")
        self.assertEqual(kwargs.get("last_name"), "Appleseed")
        self.assertEqual(kwargs.get("email"), "johnnie.appleseed@calbrightcollege.org")
        self.assertEqual(kwargs.get("status"), "")
        self.assertEqual(kwargs.get("message"), "")

    def fetch_student_tags(self, strut_id):
        self.tests_to_pass["strut_tags_fetched"] = True
        self.assertTrue(strut_id, self.test_event_data.get("strut_enrollment").lms_id)
        return self.test_event_data.get("strut_tags")

    def remove_all_student_tags(self, strut_id, tags):
        self.tests_to_pass["strut_tags_removed"] = True
        self.assertTrue(strut_id, self.test_event_data.get("strut_enrollment").lms_id)
        self.assertEqual(tags, {t.get("id") for t in self.test_event_data.get("strut_tags")})

    def assign_student_tags(self, strut_id, intended_program):
        self.tests_to_pass["strut_tags_assigned"] = True
        self.assertEqual(strut_id, self.test_event_data.get("strut_enrollment").lms_id)
        self.assertEqual(intended_program, self.test_event_data.get("intended_program"))

    def assign_student_state(self, strut_id, state):
        self.tests_to_pass["strut_state_assigned"] = True
        self.assertEqual(strut_id, self.test_event_data.get("strut_enrollment").lms_id)
        self.assertEqual(state, "active")

    def update_enrollment(self, student_strut_id, enrollment_id):
        self.tests_to_pass["update_enrollment"] = True
        self.assertEqual(student_strut_id, self.test_event_data.get("strut_enrollment").lms_id)
        self.assertEqual(enrollment_id, self.test_event_data.get("strut_competency_id"))

    def fetch_enrollments(self, student_id, shallow, count):
        self.tests_to_pass["fetch_enrollments"] = True
        self.assertEqual(student_id, self.test_event_data.get("strut_enrollment").lms_id)
        self.assertTrue(shallow)
        self.assertEqual(count, 100)
        comp_id = 214 if self.test_event_data.get("intended_program") == "IT Support" else 207
        return [
            {"competency": {"id": comp_id}, "state": "locked", "id": self.test_event_data.get("strut_competency_id")}
        ]

    def create_enrollment(self, student_strut_id, competency_id):
        self.tests_to_pass["create_enrollment"] = True
        self.assertEqual(student_strut_id, self.test_event_data.get("strut_enrollment").lms_id)
        self.assertEqual(competency_id, 210)

    def fetch_product_ids(self, strut_id):
        self.tests_to_pass["fetch_product_ids"] = True
        self.assertEqual(strut_id, self.test_event_data.get("strut_enrollment").lms_id)
        return {"product_purchases": [{"product": {"id": 3}}]}

    def add_product_to_student(self, strut_id, product_id):
        self.tests_to_pass["add_product_to_student"] = True
        self.assertEqual(strut_id, self.test_event_data.get("strut_enrollment").lms_id)
        self.assertEqual(product_id, 4)

    def session_execute(self, *args, **kwargs):
        scalar_one = MagicMock()
        self.session_executed = True
        if self.test_name == "NoResultsFound":
            scalar_one.scalar_one.side_effect = Mock(side_effect=NoResultFound("Test"))
        elif self.test_name == "EnrollmentTest":
            scalar_one.scalar_one.return_value = self.test_event_data.get("enrollment_status")
            self.test_name = "EnrollmentTestStudent"
        elif self.test_name == "EnrollmentTestStudent":
            scalar_one.scalar_one.return_value = self.test_event_data.get("instructor")
        elif self.test_name == "MissingInstructor":
            scalar_one.scalar_one.return_value = None
        elif self.test_name in ["TestRun", "EnrollInTrailhead"]:
            scalar_one.scalar_one.return_value = self.test_event_data.get("learner_status")
        else:
            scalar_one.scalar_one.return_value = self.test_event_data.get("student")
        return scalar_one

    def get_student_salesforce_fields(self, ccc_id):
        self.assertEqual(ccc_id, self.test_event_data.get("student").ccc_id)
        payload = {}
        if self.test_name == "InvalidProgram":
            return payload
        payload["cfg_Intended_Program__c"] = self.test_event_data.get("intended_program")
        if self.test_name == "MissingTags":
            return payload
        payload["cfg_Assigned_Learner_Advocate__r"] = {}
        payload["cfg_Assigned_Learner_Advocate__r"]["Id"] = "ASC_1234"
        return payload

    def create_program_enrollment(self, program_name, contact, date_of_enrollment, enrollment_status, program_version):
        self.assertEqual(program_name, self.test_event_data.get("intended_program"))
        self.assertEqual(contact, self.test_event_data.get("student").user.salesforce_id)
        self.assertEqual(date_of_enrollment, self.test_event_data.get("date_modified"))
        self.assertEqual(enrollment_status, "In Progress")
        self.assertEqual(program_version, "IT500 V1, WF500 V2")
        if self.test_name == "SfEnrollmentError":
            return {}
        return {"id": self.test_event_data.get("sf_enrollment_id")}

    def create_end_of_term_grade(self, course, ccc_id, sf_id, term_id, term_name, instructor_id=None):
        self.assertEqual(course, "IT500")
        self.assertEqual(ccc_id, self.test_event_data.get("student").ccc_id)
        self.assertEqual(sf_id, self.test_event_data.get("student").user.salesforce_id)
        self.assertEqual(term_id, self.test_event_data.get("sf_term_data").get("Id"))
        self.assertEqual(term_name, self.test_event_data.get("sf_term_data").get("Name"))
        self.assertIsNone(instructor_id)
        return self.test_event_data.get("sf_eotg_grade_resp")

    def alert_student_signed_csep(self, channel, info):
        self.slack_assigned_csep = True
        self.assertEqual(channel, "enrollment-agreement")
        self.assertDictEqual(
            info,
            {"intended_program": "IT Support", "name": "Johnnie Appleseed", "ccc_id": "AUD2286", "id": "ABC_1234_YXZ"},
        )

    def update_contact_record(self, salesforce_id, **kwargs):
        self.update_contact_record = True
        self.assertEqual(salesforce_id, self.test_event_data.get("student").user.salesforce_id)
        if self.test_name == "EnrollInTrailhead":
            self.assertEqual(
                kwargs,
                {
                    "cfg_Learner_Status__c": "Enrolled in Program Pathway",
                    "Program_Version__c": "IT520 - v1.0, IT520 - v3.0",
                },
            )
        elif self.test_name == "TestRun":
            self.assertEqual(
                kwargs,
                {
                    "Date_of_Enrollment__c": "2024-06-17T03:23:45",
                    "cfg_Learner_Status__c": "Completed CSEP",
                    "cfg_Learner_Access_Services_Requested__c": True,
                    "LMS__c": "Strut",
                    "Current_Term__c": "TERM_ID_12345",
                    "CSEP_Signed_Date__c": "2024-06-17T03:23:45",
                    "cfg_Intended_Program__c": "IT Support",
                    "Veterans_Services_Requested__c": True,
                },
            )


if __name__ == "__main__":
    unittest.main()
