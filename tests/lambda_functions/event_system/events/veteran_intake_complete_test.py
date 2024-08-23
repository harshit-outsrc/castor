import unittest
from unittest.mock import MagicMock, Mock

from lambda_functions.event_system.constants.hubspot_template_ids import (
    SCHEDULE_APPOINTMENT_TO_STUDENT,
    INTAKE_FORM_COMPLETE_TO_VS_TEAM,
)
from lambda_functions.event_system.events.veteran_intake_complete import VeteranIntakeComplete

from exceptions import MissingRequiredField, CalbrightEmailNotInSalesforce, MultipleCalbrightEmailInSalesforce


class TestEventVeteranIntakeComplete(unittest.TestCase):
    def setUp(self):
        hubspot = MagicMock()
        hubspot.send_transactional_email = Mock(side_effect=self.send_transactional_email)

        salesforce = MagicMock()
        salesforce.custom_query = Mock(side_effect=self.make_custom_query)
        salesforce.update_vet_record = Mock(side_effect=self.update_vet_record)
        salesforce.create_vet_record = Mock(side_effect=self.create_vet_record)

        pdf_service = MagicMock()
        pdf_service.add_page = Mock(side_effect=self.mock_pdf_service)
        pdf_service.set_font = Mock(side_effect=self.mock_pdf_service)
        pdf_service.cell = Mock(side_effect=self.mock_pdf_service)
        pdf_service.output = Mock(side_effect=self.mock_pdf_service)

        gdrive = MagicMock()
        gdrive.upload_file = Mock(side_effect=self.upload_file)

        self.veteran_services_email = "vs@cal.org"
        self.gdrive_folder = "g_drive_folder_calbright_xyz"
        self.expected_file_name = "/tmp/98765XSR_Calbright_test_student_"

        self.veterans_intake = VeteranIntakeComplete(
            configs={
                "constants": {"email": {"veterans": self.veteran_services_email}},
                "veteran_intake_complete": {"g_drive_parent_folder": self.gdrive_folder},
            },
            pdf=pdf_service,
            salesforce=salesforce,
            hubspot=hubspot,
            gdrive=gdrive,
        )

        self.sf_id = "!@#!@DSSF@#"
        self.vet_record_id = "1234VET9876"
        self.test_data = {
            "event_type": "veterans_intake_form_complete",
            "form_id": "HDSHJK_!234",
            "response_id": "GF123846",
            "intake_form_submitted": "YESTERDAY!!",
            "calbright_email": "calbright_student@calbrightcollege.org",
            "status": "InCharge",
            "other_status": "InCharge",
            "program_of_study": "all_of_them",
            "diabilities": "Yes",
            "student_supports": "No Please",
            "community_support": "Yes Please",
            "branch_of_service": ["US Marine Corps", "this is an other selection"],
            "fname": "Calbright",
            "information": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",  # noqa: E501
            "lname": "test_student",
            "ccc_id": "98765XSR",
            "other_program_of_study": "all_of_them",
            "other_branch_of_service": "this is an other selection",
        }
        self.vs_email_sent = self.calendly_email_sent = self.updated_vet_record = self.upload_file_called = (
            self.created_vet_record
        ) = False
        self.pdf_service_called = 0

    def test_required_fields(self):
        payload = {}
        for field in self.veterans_intake._required_fields:
            error_caught = False
            try:
                self.veterans_intake.run(payload)
            except MissingRequiredField as err:
                error_caught = True
                self.assertEqual(
                    str(err),
                    f'Event type "veterans_intake_complete" is missing or size is 0 for the required field: {field}',
                )  # noqa: E501
            self.assertTrue(error_caught)
            payload[field] = field

    def test_vet_intake_form_errors(self):
        self.test_name = "no_records"
        error_caught = False
        try:
            self.veterans_intake.run(self.test_data)
        except CalbrightEmailNotInSalesforce as err:
            self.assertEqual(
                str(err),
                "Calbright Email: calbright_student@calbrightcollege.org was not found",
            )
            error_caught = True
        self.assertTrue(error_caught)

        self.test_name = "too_many_records"
        error_caught = False
        try:
            self.veterans_intake.run(self.test_data)
        except MultipleCalbrightEmailInSalesforce as err:
            self.assertEqual(
                str(err),
                "Calbright Email: calbright_student@calbrightcollege.org returns multiple records in Salesforce",
            )
            error_caught = True
        self.assertTrue(error_caught)

    def test_successful_update_flow(self):
        self.upload_file_called = self.vs_email_sent = self.calendly_email_sent = False
        self.test_name = "successful_tests"
        self.veterans_intake.run(self.test_data)
        self.assertTrue(
            self.vs_email_sent and self.calendly_email_sent and self.updated_vet_record and self.upload_file_called
        )
        self.assertEqual(self.pdf_service_called, 42)

    def test_successful_create_flow(self):
        self.upload_file_called = self.vs_email_sent = self.calendly_email_sent = False
        self.test_name = "successful_create_test"
        self.veterans_intake.run(self.test_data)
        self.assertTrue(
            self.vs_email_sent and self.calendly_email_sent and self.create_vet_record and self.upload_file_called
        )
        self.assertEqual(self.pdf_service_called, 42)

    def mock_pdf_service(self, *args, **kwargs):
        self.pdf_service_called += 1
        self.assertTrue(
            args == ()
            or args == ("Helvetica",)
            or args == (200, 10)
            or self.expected_file_name in args[0]
            and args[0].endswith(".pdf")
        )
        self.assertTrue(kwargs == {} or kwargs == {"size": 12} or 3 <= self.pdf_service_called)

    def upload_file(self, file_name, metadata):
        self.assertTrue(self.expected_file_name in file_name and file_name.endswith(".pdf"))
        self.assertEqual(metadata.get("parents")[0].get("id"), self.gdrive_folder)
        self.assertEqual(file_name.split("/")[-1], metadata.get("title"))
        self.upload_file_called = True

    def validate_sf_data(self, args):
        for key, val in args.items():
            if key == "branch_of_service":
                self.assertTrue(val == ["Other", "USMC"] or val == ["USMC", "Other"])
            elif key == "status" or key == "program_of_study":
                self.assertEqual(val, "Other")
            else:
                self.assertEqual(self.test_data.get(key), val)

    def create_vet_record(self, salesforce_id, **kwargs):
        self.assertEqual(salesforce_id, self.sf_id)
        self.validate_sf_data(kwargs)
        self.created_vet_record = True

    def update_vet_record(self, veterans_id, **kwargs):
        self.assertEqual(veterans_id, self.vet_record_id)
        self.validate_sf_data(kwargs)
        self.updated_vet_record = True

    def send_transactional_email(self, email_id, to_email, email_name, custom_properties=None, salesforce_task=None):
        if email_id == INTAKE_FORM_COMPLETE_TO_VS_TEAM:
            self.assertEqual(to_email, self.veteran_services_email)
            self.assertEqual(custom_properties.get("first_name"), self.test_data.get("fname"))
            self.assertEqual(custom_properties.get("last_name"), self.test_data.get("lname"))
            self.assertEqual(custom_properties.get("ccc_id"), self.test_data.get("ccc_id"))
            self.assertIsNone(salesforce_task)
            self.assertEqual(email_name, "VeteransServices: Intake Form Submitted")
            self.vs_email_sent = True
        else:
            self.assertEqual(email_id, SCHEDULE_APPOINTMENT_TO_STUDENT)
            self.assertEqual(to_email, self.test_data.get("calbright_email"))
            self.assertIsNone(custom_properties)
            self.assertEqual(email_name, "VeteransServices: Schedule Appointment")
            self.assertIn("client", salesforce_task)
            self.assertIn("task_data", salesforce_task)
            self.assertEqual(
                salesforce_task.get("task_data").get("subject"), "Emailed Veteran Services Appointment Link"
            )
            self.assertEqual(salesforce_task.get("task_data").get("salesforce_id"), self.sf_id)
            self.calendly_email_sent = True

    def make_custom_query(self, query):
        self.assertEqual(
            query,
            """Select Id, firstname, lastname, cfg_ccc_id__c, (Select Id From Veteran_Service_Records__r)
            FROM Contact WHERE cfg_Calbright_Email__c = 'calbright_student@calbrightcollege.org'""",
        )
        if self.test_name == "no_records":
            return {"totalSize": 0}
        elif self.test_name == "too_many_records":
            return {"totalSize": 3}
        elif self.test_name == "successful_create_test":
            return {
                "totalSize": 1,
                "records": [
                    {
                        "Id": self.sf_id,
                        "FirstName": self.test_data.get("fname"),
                        "LastName": self.test_data.get("lname"),
                        "cfg_CCC_ID__c": self.test_data.get("ccc_id"),
                        "Veteran_Service_Records__r": None,
                    }
                ],
            }
        else:
            return {
                "totalSize": 1,
                "records": [
                    {
                        "Id": self.sf_id,
                        "FirstName": self.test_data.get("fname"),
                        "LastName": self.test_data.get("lname"),
                        "cfg_CCC_ID__c": self.test_data.get("ccc_id"),
                        "Veteran_Service_Records__r": {"records": [{"Id": self.vet_record_id}]},
                    }
                ],
            }


if __name__ == "__main__":
    unittest.main()
