import datetime
from uuid import UUID

import unittest
from unittest import mock
from unittest.mock import MagicMock
from mock_alchemy.mocking import UnifiedAlchemyMagicMock

from propus.calbright_sql.calbright import Calbright
from lambda_functions.calbright_trigger_workflow.workflows.process_new_ccc_applications import NewCCCApplications


class TestNewCCCApplications(unittest.TestCase):
    def setUp(self):
        self.configs = {"some_random_configs": "this.is.a.value"}
        self.psql_engine = MagicMock()
        self.new_ccc_application = NewCCCApplications(self.configs, self.psql_engine)

        self.test_trigger_data = {
            "psql_trigger_type": "new_ccc_application_trigger",
            "id": UUID("10000000-0000-0000-0000-100000000000"),
            "created_at": "2023-05-18 14:26:39.749475",
            "trigger_op": "INSERT",
        }
        self.app_data = {
            "address_val_override": False,
            "app_id": 11223344,
            "available_afternoons": False,
            "available_evenings": False,
            "available_mornings": True,
            "available_weekends": False,
            "birthdate": datetime.date(1731, 2, 11),
            "blocked_application": False,
            "ccc_id": "TST1234",
            "city": "Test City",
            "contact_email": True,
            "contact_phone_call": False,
            "contact_text_message": False,
            "country": "US",
            "created_at": datetime.datetime(2023, 5, 18, 14, 26, 39, 749475),
            "email": "test@calbright.org",
            "firstname": "George",
            "fraud_score": 0,
            "fraud_status": 6,
            "gender": "X",
            "id": UUID("10000000-0000-0000-0000-100000000000"),
            "ip_address": "127.0.0.1",
            "lastname": "Testington",
            "mainphone": None,
            "middlename": None,
            "no_mailing_address_homeless": False,
            "no_perm_address_homeless": True,
            "perm_city": None,
            "perm_country": None,
            "perm_postalcode": None,
            "perm_state": None,
            "perm_streetaddress1": None,
            "perm_streetaddress2": None,
            "postalcode": "12345",
            "pref_contact_method": "email",
            "preferred_firstname": None,
            "processed_application": False,
            "race_ethnic": "NNNNNNNNNNNNNNNNNNNNY",
            "race_ethnic_full": "800,807,808",
            "race_group": "21",
            "ssn": None,
            "ssn_type": None,
            "state": "CA",
            "streetaddress1": "123 Test st",
            "streetaddress2": None,
            "suffix": None,
            "tstmp_submit": datetime.datetime(2023, 4, 7, 20, 21, 57, 631000),
        }
        self.ccc_application = self.convert_dict_to_object(Calbright.CCCApplication(), self.app_data)

        self.new_ccc_application.psql_engine.session = UnifiedAlchemyMagicMock(
            data=[
                ([mock.call.query(Calbright.Student)], []),
                ([mock.call.query(Calbright.User)], []),
                ([mock.call.query(Calbright.CCCApplication)], [self.ccc_application]),
            ]
        )

    def test_get_ccc_application_based_on_id(self):
        returned_data = self.new_ccc_application.get_ccc_application_based_on_id(self.test_trigger_data.get("id"))
        self.assertEqual(self.ccc_application, returned_data)

    def test_check_for_existing_records(self):
        model_app = self.convert_dict_to_object(Calbright.CCCApplication(), self.app_data)
        test_student = Calbright.Student(
            ccc_id="TST1234",
            date_of_birth=datetime.date(1731, 2, 11),
        )
        test_user = Calbright.User(
            first_name="George",
            last_name="Testington",
            phone_number=None,
            student=test_student,
            personal_email="test@calbright.org",
        )

        self.new_ccc_application.psql_engine.session.add(test_student)
        self.new_ccc_application.check_for_existing_records(model_app)
        self.assertFalse(self.new_ccc_application.new_student)

        self.new_ccc_application.psql_engine.session.add(test_user)
        self.new_ccc_application.check_for_existing_records(model_app)
        self.assertFalse(self.new_ccc_application.new_student)

    def test_create_student_record(self):
        self.assertTrue(self.new_ccc_application.create_student_record(self.ccc_application, Calbright.User()))

    def convert_dict_to_object(self, model_object, test_data):
        for key, value in test_data.items():
            setattr(model_object, key, value)
        return model_object


if __name__ == "__main__":
    unittest.main()
