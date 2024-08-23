import datetime
from uuid import UUID

import unittest
from unittest import mock
from unittest.mock import MagicMock
from mock_alchemy.mocking import UnifiedAlchemyMagicMock

from propus.calbright_sql.calbright import Calbright
from lambda_functions.calbright_trigger_workflow.workflows.process_update_create_grades import UpdateCreateGrades
from src.exceptions import UnrecognizedGrade


class TestUpdateCreateGrades(unittest.TestCase):
    def setUp(self):
        self.configs = {"some_random_configs": "this.is.a.value"}
        self.psql_engine = MagicMock()
        self.anthology = MagicMock()
        self.update_create_grades = UpdateCreateGrades(self.configs, self.psql_engine, self.anthology)
        self.grade_posted = False

        self.test_trigger_data = {
            "psql_trigger_type": "update_create_grade_trigger",
            "id": UUID("10000000-0000-0000-0000-100000000000"),
            "created_at": "2023-05-18 14:26:39.749475",
            "trigger_op": "UPDATE",
        }

        self.staff_data = {
            "id": "90010000-0000-0000-0000-100000000000",
            "staff_title": "instructor",
            "staff_role": None,
            "calendly_link": None,
            "staff_slack_id": "Something123",
            "active_staff": True,
            "created_at": datetime.datetime(2023, 5, 18, 14, 26, 39, 749475),
        }
        self.staff_record = self.convert_dict_to_object(Calbright.Staff(), self.staff_data)

        self.user_data = {
            "id": "20000000-0000-0000-0000-100000000000",
            "ccc_id": "TST1234",
            "anthology_id": "20000000-1111-2222-3333-100000000000",
            "gender_id": "20000000-0000-0000-0000-100000000001",
            "pronoun_id": "20000000-0000-0000-0000-100000000002",
            "salutation_id": "20000000-0000-0000-0000-100000000003",
            "suffix_id": "20000000-0000-0000-0000-100000000004",
            "first_name": "George",
            "middle_name": "",
            "last_name": "Testington",
            "calbright_email": "test@calbrightcollege.org",
            "phone_number": "5555555555",
            "created_at": datetime.datetime(2023, 5, 18, 14, 26, 39, 749475),
        }
        self.user_record = self.convert_dict_to_object(Calbright.User(), self.user_data)

        self.student_data = {
            "id": "30000000-0000-0000-0000-100000000000",
            "user_student": [self.user_record],
            "ccc_id": "TST1234",
            "date_of_birth": datetime.date(1731, 2, 11),
            "personal_email": "test@calbrightcollege.org",
            "created_at": datetime.datetime(2023, 5, 18, 14, 26, 39, 749475),
        }
        self.student_record = self.convert_dict_to_object(Calbright.Student(), self.student_data)

        self.program_data = {
            "id": "50000000-0000-0000-0000-100000000001",
            "program_name": "Testing Program Name",
            "anthology_program_id": 1,
            "anthology_program_version_id": 2,
        }
        self.program_record = self.convert_dict_to_object(Calbright.Program(), self.program_data)

        self.program_version_data = {
            "id": "40000000-0000-0000-0000-100000000001",
            "program": self.program_record,
        }
        self.program_version_record = self.convert_dict_to_object(Calbright.ProgramVersion(), self.program_version_data)

        self.first_term_data = {
            "id": "60000000-0000-0000-0000-210000000000",
            "term_name": "First Test Term",
            "start_date": datetime.date(2022, 11, 7),
            "end_date": datetime.date(2023, 5, 7),
            "anthology_id": 65,
        }
        self.first_term_record = self.convert_dict_to_object(Calbright.Term(), self.first_term_data)

        self.term_data = {
            "id": "60000000-0000-0000-0000-100000000002",
            "term_name": "Test Term",
            "start_date": datetime.date(2023, 12, 7),
            "end_date": datetime.date(2024, 6, 7),
            "anthology_id": 120,
        }
        self.term_record = self.convert_dict_to_object(Calbright.Term(), self.term_data)

        self.enrollment_data = {
            "id": "10010000-0000-0000-0000-100000000000",
            "ccc_id": "TST1234",
            "student": self.student_record,
            "program_version": self.program_version_record,
            "first_term": self.first_term_record,
            "enrollment_status_id": "10000000-0000-0000-0000-100000000003",
            "counselor_id": "10000000-0000-0000-0000-100000000004",
            "lms_id": "10000000-0000-0000-0000-100000000005",
            "first_saa": None,
            "last_saa": None,
            "progress": 0.0,
            "pace_timeline_id": "10000000-0000-0000-0000-100000000006",
            "enrollment_date": datetime.datetime(1831, 2, 11, 14, 26, 39, 749475),
            "completion_date": None,
            "intended_completion_date": datetime.datetime(1931, 2, 11, 14, 26, 39, 749475),
            "created_at": datetime.datetime(2023, 5, 18, 14, 26, 39, 749475),
        }
        self.enrollment_record = self.convert_dict_to_object(Calbright.Enrollment(), self.enrollment_data)

        self.grade_data = {
            "id": "20010000-0000-0000-0000-200000000000",
            "grade": "P",
            "title": "Pass",
            "created_at": datetime.datetime(2023, 5, 18, 14, 26, 39, 749475),
        }
        self.grade_record = self.convert_dict_to_object(Calbright.Grade(), self.grade_data)

        self.course_data = {
            "id": "20020000-0000-0000-0000-200000000000",
            "course_name": "Some IT Course",
            "status": "active",
            "course_id": 22,
            "course_code": "SIT501",
            "anthology_course_id": 3,
        }
        self.course_record = self.convert_dict_to_object(Calbright.Course(), self.course_data)

        self.course_version_data = {
            "id": "20020000-0000-0000-0000-200000000000",
            "course": self.course_record,
            "version_id": "20020000-1000-0000-0000-200000000000",
        }
        self.course_version_record = self.convert_dict_to_object(Calbright.CourseVersion(), self.course_version_data)

        self.enrollment_course_term_data = {
            "id": "10000000-0000-0000-0000-100000000000",
            "enrollment": self.enrollment_record,
            "anthology_course_id": 123,
            "grade_salesforce_id": "456ABC",
            "term": self.term_record,
            "term_id": self.term_record.id,
            "grade_status": "Certified",
            "certified_by": self.staff_record,
            "grade": self.grade_record,
            "withdraw_date": None,
            "drop_date": None,
            "grade_date": None,
            "certified_date": None,
            "created_at": datetime.datetime(2023, 5, 18, 14, 26, 39, 749475),
            "course_version": self.course_version_record,
        }
        self.enrollment_course_term_record = self.convert_dict_to_object(
            Calbright.EnrollmentCourseTerm(), self.enrollment_course_term_data
        )

        self.update_create_grades.psql_engine.session = UnifiedAlchemyMagicMock(
            data=[
                ([mock.call.query(Calbright.EnrollmentCourseTerm)], [self.enrollment_course_term_record]),
            ]
        )

        self.update_create_grades.anthology.fetch_drop_reason = MagicMock(side_effect=self.call_fetch_drop_reason)
        self.update_create_grades.anthology.drop_course = MagicMock(side_effect=self.call_drop_course)
        self.update_create_grades.anthology.post_final_grade = MagicMock(side_effect=self.call_post_final_grade)

        self.update_create_grades.anthology.fetch_course_for_enrollment = MagicMock(
            side_effect=self.call_fetch_course_for_enrollment
        )
        self.update_create_grades.anthology.fetch_term_for_courses = MagicMock(
            side_effect=self.call_fetch_term_for_courses
        )
        self.update_create_grades.anthology.fetch_classes_for_courses = MagicMock(
            side_effect=self.call_fetch_classes_for_courses
        )
        self.update_create_grades.anthology.register_course = MagicMock(side_effect=self.call_register_course)

    def test_passing_grades(self):
        self.grade_posted = False
        self.update_create_grades.enrollment_course_term_record = self.enrollment_course_term_record
        self.update_create_grades.update_or_create_sis_grades()

        self.assertEqual(self.enrollment_course_term_record, self.update_create_grades.enrollment_course_term_record)
        self.assertTrue(self.grade_posted)

    def test_dropping_grades(self):
        self.enrollment_course_term_record.grade.grade = "D"
        self.enrollment_course_term_record.grade.title = "Dropped"
        self.grade_posted = False

        self.update_create_grades.enrollment_course_term_record = self.enrollment_course_term_record
        self.update_create_grades.update_or_create_sis_grades()

        self.assertEqual(self.enrollment_course_term_record, self.update_create_grades.enrollment_course_term_record)
        self.assertTrue(self.grade_posted)

        self.enrollment_course_term_record.grade.grade = "W"
        self.enrollment_course_term_record.grade.title = "Withdraw"
        self.grade_posted = False

        self.update_create_grades.enrollment_course_term_record = self.enrollment_course_term_record
        self.update_create_grades.update_or_create_sis_grades()

        self.assertEqual(self.enrollment_course_term_record, self.update_create_grades.enrollment_course_term_record)
        self.assertTrue(self.grade_posted)

        self.enrollment_course_term_record.grade.grade = "NP"
        self.enrollment_course_term_record.grade.title = "Not Passed"
        self.grade_posted = False

        self.update_create_grades.enrollment_course_term_record = self.enrollment_course_term_record
        self.update_create_grades.update_or_create_sis_grades()

        self.assertEqual(self.enrollment_course_term_record, self.update_create_grades.enrollment_course_term_record)
        self.assertTrue(self.grade_posted)

    def test_bypassing_grades(self):
        self.enrollment_course_term_record.grade.grade = "I"
        self.enrollment_course_term_record.grade.title = "Incomplete"
        self.grade_posted = False

        self.update_create_grades.enrollment_course_term_record = self.enrollment_course_term_record
        self.update_create_grades.update_or_create_sis_grades()

        self.assertEqual(self.enrollment_course_term_record, self.update_create_grades.enrollment_course_term_record)
        self.assertFalse(self.grade_posted)

    def test_erroring_grades(self):
        self.enrollment_course_term_record.grade.grade = "NG"
        self.enrollment_course_term_record.grade.title = "Not a Grade"
        self.update_create_grades.enrollment_course_term_record = self.enrollment_course_term_record
        with self.assertRaises(UnrecognizedGrade):
            self.update_create_grades.update_or_create_sis_grades()

    def test_create_sis_courses(self):

        self.update_create_grades.enrollment_course_term_record = self.enrollment_course_term_record
        self.update_create_grades.create_sis_courses(student_id=111, enrollment_id=222)

    def convert_dict_to_object(self, model_object, test_data):
        for key, value in test_data.items():
            setattr(model_object, key, value)
        return model_object

    async def call_drop_course(self, *args, **kwargs):
        self.grade_posted = True
        return 200

    async def call_post_final_grade(self, *args, **kwargs):
        self.grade_posted = True
        return 200

    async def call_fetch_drop_reason(self, *args, **kwargs):
        return {
            "value": [
                {
                    "Id": 5,
                    "CampusGroupId": 388,
                    "Code": "DROP",
                    "CreatedDateTime": "2021-01-08T15:51:17-06:00",
                    "IsActive": True,
                    "IsForDelete": False,
                    "IsForDrop": True,
                    "IsForUnregister": False,
                    "IsLdaRetainedUnregCourses": False,
                    "LastModifiedDateTime": "2024-02-28T10:24:59.13-06:00",
                    "LastModifiedUserId": 59,
                    "Name": "Dropped",
                },
                {
                    "Id": 6,
                    "CampusGroupId": 389,
                    "Code": "W",
                    "CreatedDateTime": "2021-01-08T15:52:35-06:00",
                    "IsActive": True,
                    "IsForDelete": False,
                    "IsForDrop": True,
                    "IsForUnregister": False,
                    "IsLdaRetainedUnregCourses": True,
                    "LastModifiedDateTime": "2023-11-01T06:53:18.993-05:00",
                    "LastModifiedUserId": 52,
                    "Name": "Withdrawn",
                },
                {
                    "Id": 7,
                    "CampusGroupId": 390,
                    "Code": "MW",
                    "CreatedDateTime": "2021-01-08T16:01:00.277-06:00",
                    "IsActive": True,
                    "IsForDelete": False,
                    "IsForDrop": False,
                    "IsForUnregister": True,
                    "IsLdaRetainedUnregCourses": True,
                    "LastModifiedDateTime": "2021-01-08T16:01:00.277-06:00",
                    "LastModifiedUserId": 59,
                    "Name": "Military Withdrawal",
                },
                {
                    "Id": 8,
                    "CampusGroupId": 391,
                    "Code": "EW",
                    "CreatedDateTime": "2021-01-08T16:01:42.66-06:00",
                    "IsActive": True,
                    "IsForDelete": False,
                    "IsForDrop": False,
                    "IsForUnregister": True,
                    "IsLdaRetainedUnregCourses": True,
                    "LastModifiedDateTime": "2021-01-08T16:01:42.66-06:00",
                    "LastModifiedUserId": 59,
                    "Name": "Excused Withdrawal",
                },
                {
                    "Id": 9,
                    "CampusGroupId": 470,
                    "Code": "AD-I",
                    "CreatedDateTime": "2021-01-28T09:24:03-06:00",
                    "IsActive": False,
                    "IsForDelete": False,
                    "IsForDrop": True,
                    "IsForUnregister": False,
                    "IsLdaRetainedUnregCourses": True,
                    "LastModifiedDateTime": "2024-02-28T10:21:39.907-06:00",
                    "LastModifiedUserId": 59,
                    "Name": "Administrative Drop - Inactivity",
                },
                {
                    "Id": 10,
                    "CampusGroupId": 471,
                    "Code": "AD-D-W",
                    "CreatedDateTime": "2021-01-28T09:24:56-06:00",
                    "IsActive": True,
                    "IsForDelete": False,
                    "IsForDrop": True,
                    "IsForUnregister": False,
                    "IsLdaRetainedUnregCourses": True,
                    "LastModifiedDateTime": "2023-11-01T06:52:50.017-05:00",
                    "LastModifiedUserId": 52,
                    "Name": "Administrative Drop - Discipline - Withdraw",
                },
                {
                    "Id": 11,
                    "CampusGroupId": 472,
                    "Code": "DROP-IP",
                    "CreatedDateTime": "2021-01-28T09:26:55-06:00",
                    "IsActive": True,
                    "IsForDelete": False,
                    "IsForDrop": True,
                    "IsForUnregister": False,
                    "IsLdaRetainedUnregCourses": False,
                    "LastModifiedDateTime": "2024-02-28T10:22:18.16-06:00",
                    "LastModifiedUserId": 59,
                    "Name": "Drop - Inactive Provisional",
                },
                {
                    "Id": 12,
                    "CampusGroupId": 959,
                    "Code": "PC-AS",
                    "CreatedDateTime": "2021-09-23T17:45:55-05:00",
                    "IsActive": True,
                    "IsForDelete": False,
                    "IsForDrop": True,
                    "IsForUnregister": False,
                    "IsLdaRetainedUnregCourses": True,
                    "LastModifiedDateTime": "2023-11-01T06:53:09.043-05:00",
                    "LastModifiedUserId": 52,
                    "Name": "Program Change - After Start",
                },
                {
                    "Id": 13,
                    "CampusGroupId": 960,
                    "Code": "PC-PRE",
                    "CreatedDateTime": "2021-09-23T17:46:39-05:00",
                    "IsActive": True,
                    "IsForDelete": False,
                    "IsForDrop": False,
                    "IsForUnregister": True,
                    "IsLdaRetainedUnregCourses": False,
                    "LastModifiedDateTime": "2024-02-28T10:20:29.013-06:00",
                    "LastModifiedUserId": 59,
                    "Name": "Program Change - Pre Start",
                },
                {
                    "Id": 14,
                    "CampusGroupId": 961,
                    "Code": "AD-D-D",
                    "CreatedDateTime": "2021-09-23T17:49:45-05:00",
                    "IsActive": True,
                    "IsForDelete": False,
                    "IsForDrop": False,
                    "IsForUnregister": True,
                    "IsLdaRetainedUnregCourses": False,
                    "LastModifiedDateTime": "2024-02-28T10:30:00.063-06:00",
                    "LastModifiedUserId": 59,
                    "Name": "Administrative Drop - Discipline - Drop",
                },
                {
                    "Id": 15,
                    "CampusGroupId": 10225,
                    "Code": "PW",
                    "CreatedDateTime": "2024-02-28T10:19:42.257-06:00",
                    "IsActive": True,
                    "IsForDelete": False,
                    "IsForDrop": True,
                    "IsForUnregister": False,
                    "IsLdaRetainedUnregCourses": None,
                    "LastModifiedDateTime": "2024-02-28T10:19:42.257-06:00",
                    "LastModifiedUserId": 59,
                    "Name": "Progress Withdrawal",
                },
            ]
        }

    async def call_fetch_course_for_enrollment(self, *args, **kwargs):
        return {
            "Items": [
                {
                    "Entity": {
                        "Id": 1,
                        "StudentEnrollmentPeriodId": 2,
                        "CourseId": 3,
                        "ClockHours": 4,
                    }
                }
            ]
        }

    async def call_fetch_term_for_courses(self, *args, **kwargs):
        return {
            "value": [
                {
                    "TermStartDate": "2023-12-7T20:21:57:631000",
                    "Id": 2024,
                },
            ]
        }

    async def call_fetch_classes_for_courses(self, *args, **kwargs):
        return {"value": [{"Id": 10}]}

    async def call_register_course(self, *args, **kwargs):
        return {"entity": {"Id": 501}}


if __name__ == "__main__":
    unittest.main()
