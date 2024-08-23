import datetime
from uuid import UUID

import unittest
from unittest import mock
from unittest.mock import MagicMock, Mock
from mock_alchemy.mocking import UnifiedAlchemyMagicMock

from propus.calbright_sql.calbright import Calbright
from lambda_functions.calbright_trigger_workflow.workflows.process_update_student_demographic import (
    UpdateStudentDemographic,
)


class TestUpdateStudentDemographic(unittest.TestCase):
    def setUp(self):
        self.configs = {"some_random_configs": "this.is.a.value"}
        self.psql_engine = MagicMock()
        self.anthology = MagicMock()
        self.update_student_demographic = UpdateStudentDemographic(self.configs, self.psql_engine, self.anthology)

        self.address_data = {
            "city": "Testington",
            "zip": "12345",
            "state": "CA",
            "address1": "123 Test st",
            "address2": "",
        }
        self.address_record = self.convert_dict_to_object(Calbright.Address(), self.address_data)

        self.student_address_data = {
            "current": True,
            "address": self.address_record,
        }
        self.student_address_record = self.convert_dict_to_object(Calbright.StudentAddress(), self.student_address_data)
        self.gender_data = {
            "anthology_id": 2,
        }
        self.gender_record = self.convert_dict_to_object(Calbright.Gender(), self.gender_data)
        self.suffix_data = {
            "anthology_id": 3,
        }
        self.suffix_record = self.convert_dict_to_object(Calbright.Suffix(), self.suffix_data)
        self.pronoun_data = {
            "anthology_id": 4,
        }
        self.pronoun_record = self.convert_dict_to_object(Calbright.Pronoun(), self.pronoun_data)
        self.ethnicity_data = {
            "anthology_id": 5,
        }
        self.ethnicity_record = self.convert_dict_to_object(Calbright.Ethnicity(), self.ethnicity_data)
        self.student_ethnicity_data = {"ethnicity": self.ethnicity_record}
        self.student_ethnicity_record = self.convert_dict_to_object(
            Calbright.StudentEthnicity(), self.student_ethnicity_data
        )

        self.test_trigger_data = {
            "psql_trigger_type": "update_student_demographic_trigger",
            "id": UUID("10000000-0000-0000-0000-100000000000"),
            "created_at": "2023-05-18 14:26:39.749475",
            "trigger_op": "UPDATE",
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
            "preferred_first_name": "DevTest",
            "preferred_last_name": "TestImplementation",
            "created_at": datetime.datetime(2023, 5, 18, 14, 26, 39, 749475),
            "pronoun": self.pronoun_record,
            "suffix": self.suffix_record,
            "gender": self.gender_record,
        }
        self.user_record = self.convert_dict_to_object(Calbright.User(), self.user_data)

        self.student_data = {
            "id": "30000000-0000-0000-0000-100000000000",
            "user": self.user_record,
            "student_address": [self.student_address_record],
            "student_ethnicity": [self.student_ethnicity_record],
            "ccc_id": "TST1234",
            "date_of_birth": datetime.date(1731, 2, 11),
            "personal_email": "test@calbrightcollege.org",
            "created_at": datetime.datetime(2023, 5, 18, 14, 26, 39, 749475),
            "ssn": "000000000",
        }
        self.student_record = self.convert_dict_to_object(Calbright.Student(), self.student_data)

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

        self.student_test_payload = {
            "first_name": self.user_record.first_name,
            "genderId": self.gender_record.anthology_id,
            "last_name": self.user_record.last_name,
            "maidenName": self.user_record.maiden_name,
            "middle_name": self.user_record.middle_name,
            "phone_number": (
                "({}) {}-{}".format(
                    self.user_record.phone_number[0:3],
                    self.user_record.phone_number[3:6],
                    self.user_record.phone_number[6:],
                )
                if self.user_record.phone_number
                else None
            ),
            "preferredName": f"{self.user_record.preferred_first_name} {self.user_record.preferred_last_name}",
            "ssn": self.student_record.ssn,
            "suffixId": self.suffix_record.anthology_id,
            "genderPronounList": [self.pronoun_record.anthology_id],
            "ethnicitiesList": [self.ethnicity_record.anthology_id],
            "city": self.address_record.city,
            "postal_code": self.address_record.zip,
            "state": self.address_record.state,
            "street_address": self.address_record.address1,
            "streetAddress2": self.address_record.address2,
        }

        self.update_student_demographic.psql_engine.session = UnifiedAlchemyMagicMock(
            data=[
                ([mock.call.query(Calbright.User)], [self.user_record]),
                ([mock.call.query(Calbright.CCCApplication)], [self.ccc_application_record]),
            ]
        )

        self.update_student_demographic.anthology.update_student = Mock(side_effect=self.call_update_student)

    def test_get_student_data(self):
        self.update_student_demographic.get_student_data(self.test_trigger_data.get("id"))

        self.assertEqual(self.student_record, self.update_student_demographic.student_record)
        self.assertEqual(self.user_record, self.update_student_demographic.user_record)
        self.assertEqual(self.ccc_application_record, self.update_student_demographic.ccc_application)

    def test_create_student_payload(self):
        self.update_student_demographic.user_record = self.user_record
        self.update_student_demographic.student_record = self.student_record
        self.update_student_demographic.ccc_application = self.ccc_application_record
        student_result = self.update_student_demographic.create_student_payload()
        self.assertEqual(self.student_test_payload, student_result)

    def test_update_sis_student(self):
        self.update_student_demographic.user_record = self.user_record
        self.update_student_demographic.student_record = self.student_record
        self.update_student_demographic.update_sis_student()

        with self.assertRaises(Exception):
            self.update_student_demographic.user_record.anthology_id = None
            self.update_student_demographic.update_sis_student()

    def convert_dict_to_object(self, model_object, test_data):
        for key, value in test_data.items():
            setattr(model_object, key, value)
        return model_object

    async def call_update_student(self, *args, **kwargs):
        return {"id": 100}


if __name__ == "__main__":
    unittest.main()
