import datetime
from uuid import UUID

import unittest
from unittest import mock
from unittest.mock import MagicMock
from mock_alchemy.mocking import UnifiedAlchemyMagicMock

from propus.calbright_sql.calbright import Calbright
from lambda_functions.calbright_trigger_workflow.workflows.process_new_certificates import NewCertificates
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestNewCertificates(unittest.TestCase):
    def setUp(self):
        self.configs = {"some_random_configs": "this.is.a.value"}
        self.psql_engine = MagicMock()
        self.anthology = MagicMock()
        self.create_certificates = NewCertificates(self.configs, self.psql_engine, self.anthology)
        self.certificate_created = False

        self.test_trigger_data = {
            "psql_trigger_type": "create_certificates_trigger",
            "id": UUID("10000000-0000-0000-0000-100000000000"),
            "created_at": "2023-05-18 14:26:39.749475",
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
            "first_term": self.term_record,
            "enrollment_status_id": "10000000-0000-0000-0000-100000000003",
            "counselor_id": "10000000-0000-0000-0000-100000000004",
            "lms_id": "10000000-0000-0000-0000-100000000005",
            "first_saa": None,
            "last_saa": None,
            "progress": 0.0,
            "pace_timeline_id": "10000000-0000-0000-0000-100000000006",
            "enrollment_date": datetime.datetime(1831, 2, 11, 14, 26, 39, 749475),
            "completion_date": datetime.datetime(1931, 2, 11, 14, 26, 39, 749475),
            "intended_completion_date": datetime.datetime(1931, 2, 11, 14, 26, 39, 749475),
            "created_at": datetime.datetime(2023, 5, 18, 14, 26, 39, 749475),
        }
        self.enrollment_record = self.convert_dict_to_object(Calbright.Enrollment(), self.enrollment_data)

        self.create_certificates.psql_engine.session = UnifiedAlchemyMagicMock(
            data=[
                ([mock.call.query(Calbright.Enrollment)], [self.enrollment_record]),
            ]
        )

        self.create_certificates.anthology.create_certificate = MagicMock(side_effect=self.call_create_certificate)

    def test_create_sis_certificates(self):
        self.create_certificates.create_sis_certificates(self.test_trigger_data.get("id"))

        self.assertTrue(self.certificate_created)

    def convert_dict_to_object(self, model_object, test_data):
        for key, value in test_data.items():
            setattr(model_object, key, value)
        return model_object

    async def call_create_certificate(self, *args, **kwargs):
        self.certificate_created = True
        return 200


if __name__ == "__main__":
    unittest.main()
