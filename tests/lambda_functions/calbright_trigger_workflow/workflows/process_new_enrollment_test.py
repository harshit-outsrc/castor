import datetime
from uuid import UUID

import unittest
from unittest import mock
from unittest.mock import MagicMock
from mock_alchemy.mocking import UnifiedAlchemyMagicMock

from propus.calbright_sql.calbright import Calbright
from lambda_functions.calbright_trigger_workflow.workflows.process_new_enrollment import NewEnrollment


class TestNewEnrollment(unittest.TestCase):
    def setUp(self):
        self.configs = {"some_random_configs": "this.is.a.value"}
        self.psql_engine = MagicMock()
        self.anthology = MagicMock()
        self.new_enrollment = NewEnrollment(self.configs, self.psql_engine, self.anthology)

        self.test_trigger_data = {
            "psql_trigger_type": "new_enrollment_trigger",
            "id": UUID("10000000-0000-0000-0000-100000000000"),
            "created_at": "2023-05-18 14:26:39.749475",
            "trigger_op": "INSERT",
        }

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
            "user": self.user_record,
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

        self.term_data = {
            "id": "60000000-0000-0000-0000-100000000002",
            "term_name": "Test Term",
            "start_date": datetime.date(2023, 12, 7),
            "end_date": datetime.date(2024, 6, 7),
            "anthology_id": 120,
        }
        self.term_record = self.convert_dict_to_object(Calbright.Term(), self.term_data)

        self.enrollment_data = {
            "id": "10000000-0000-0000-0000-100000000000",
            "ccc_id": "TST1234",
            "anthology_enrollment_number": None,
            "student": self.student_record,
            "program_version": self.program_version_record,
            "first_term": self.term_record,
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

        self.ccc_application_data = {
            "app_id": 11223344,
            "ccc_id": "TST1234",
            "created_at": datetime.datetime(2023, 5, 18, 14, 26, 39, 749475),
            "email": "test@calbright.org",
            "firstname": "George",
            "id": "10000000-0000-0000-0000-100000000000",
            "lastname": "Testington",
            "mainphone": None,
            "middlename": None,
            "ssn": None,
            "ssn_type": None,
            "highest_edu_level": "81883",
            "tstmp_submit": datetime.datetime(2023, 4, 7, 20, 21, 57, 631000),
        }
        self.ccc_application_record = self.convert_dict_to_object(Calbright.CCCApplication(), self.ccc_application_data)

        self.new_enrollment.psql_engine.session = UnifiedAlchemyMagicMock(
            data=[
                ([mock.call.query(Calbright.Enrollment)], [self.enrollment_record]),
                ([mock.call.query(Calbright.CCCApplication)], [self.ccc_application_record]),
            ]
        )

        self.new_enrollment.anthology.fetch_configurations = MagicMock(side_effect=self.call_anthology_configuration)
        self.new_enrollment.anthology.student_by_id = MagicMock(side_effect=self.call_student_by_id)
        self.new_enrollment.anthology.create_student = MagicMock(side_effect=self.call_create_student)
        self.new_enrollment.anthology.create_enrollment = MagicMock(side_effect=self.call_create_enrollment)

    def test_get_enrollment_based_on_id(self):
        self.new_enrollment.get_enrollment_based_on_id(self.test_trigger_data.get("id"))

        self.assertEqual(self.enrollment_record, self.new_enrollment.enrollment_record)
        self.assertEqual(self.student_record, self.new_enrollment.student_record)
        self.assertEqual(self.user_record, self.new_enrollment.user_record)
        self.assertEqual(self.ccc_application_record, self.new_enrollment.ccc_application)

    def test_get_required_data(self):
        enrollment = {
            "student_id": "",
            "program_id": "",
            "program_version_id": "",
            "grade_level_id": "",
            "start_date": "",
            "grad_date": "",
            "catalog_year_id": "",
            "version_start_date": "",
            "application_received_date": "",
            "enrollment_date": "",
        }
        self.new_enrollment.enrollment_record = self.enrollment_record
        self.new_enrollment.user_record = self.user_record
        self.new_enrollment.student_record = self.student_record
        self.new_enrollment.ccc_application = self.ccc_application_record
        self.new_enrollment.get_required_data(enrollment)

    def test_create_sis_student(self):
        self.new_enrollment.user_record = self.user_record
        self.new_enrollment.student_record = self.student_record
        self.new_enrollment.create_sis_student()

        self.new_enrollment.user_record.anthology_id = None
        self.new_enrollment.create_sis_student()

    def test_create_enrollment(self):
        self.new_enrollment.enrollment_record = self.enrollment_record
        self.new_enrollment.ccc_application = self.ccc_application_record
        self.new_enrollment.create_sis_enrollment()

    def convert_dict_to_object(self, model_object, test_data):
        for key, value in test_data.items():
            setattr(model_object, key, value)
        return model_object

    async def call_anthology_configuration(self, *args, **kwargs):
        if args[0] == "catalog_year":
            return {
                "value": [
                    {
                        "EffectiveEndDate": "2024-12-7T20:21:57:631000",
                        "EffectiveStartDate": "1453-12-7T20:21:57:631000",
                        "Id": 1024,
                    },
                ]
            }
        elif args[0] == "start_date":
            return {
                "value": [
                    {
                        "StartDate": "2023-12-7T20:21:57:631000",
                        "Id": 2024,
                    },
                ]
            }

    async def call_student_by_id(self, *args, **kwargs):
        return {"id": 100}

    async def call_create_student(self, *args, **kwargs):
        return {"id": 101}

    async def call_create_enrollment(self, *args, **kwargs):
        return {"id": 102}


if __name__ == "__main__":
    unittest.main()
