import unittest
from unittest.mock import MagicMock, Mock

from lambda_functions.event_system.constants.hubspot_template_ids import (
    AUTOMATIC_DROP_DEVICE,
    AUTOMATIC_DROP_STAFF,
    AUTOMATIC_DROP_STUDENT,
)
from lambda_functions.event_system.events.salesforce import SalesforceEvent

from exceptions import MissingRequiredField


class TestEventSalesforce(unittest.TestCase):
    def setUp(self):
        calbright = MagicMock()
        calbright.session.execute.scalar_one = Mock(return_value=None)

        hubspot = MagicMock()
        hubspot.send_transactional_email = Mock(side_effect=self.send_transactional_email)

        gsuite_users = MagicMock()
        gsuite_users.suspend_student = Mock(return_value={"student": "updated"})

        gsuite_licensing = MagicMock()
        gsuite_licensing.delete_license = Mock(return_value=None)

        salesforce = MagicMock()
        salesforce.client.update_contact_record = Mock(return_value=None)

        strut = MagicMock()
        strut.lock_student_enrollments = Mock(return_value=None)
        strut.withdraw_student = Mock(return_value=None)

        sf_id = "0033a00003IDZOFOO3"
        name = "Jane Dougherty"
        program = "T2T CRM Admin"
        email = "jane.dougherty@gmail.com"
        ccc_id = "FOOBAR1"
        calbright_email = "jane.dougherty@calbright.org"
        strut_id = 123
        counselor_id = "0033a00003IDZOBAR3"
        self.counselor_email = "counselor@calbright.org"
        drop_reason = "Student Dropped"
        email_prefix = "Per your request, we have withdrawn you from your course of study."
        email_suffix = ""
        self.student_data = {
            "Student__r": {"Id": sf_id, "Name": name, "cfg_Intended_Program__c": program, "Email": email}
        }
        self.contact_data = {
            "cfg_CCC_ID__c": ccc_id,
            "cfg_Calbright_Email__c": calbright_email,
            "cfg_Strut_User_ID__c": strut_id,
            "cfg_Assigned_Learner_Advocate__c": counselor_id,
        }
        self.test_data = {
            "sf_id": sf_id,
            "ccc_id": ccc_id,
            "strut_id": strut_id,
            "name": name,
            "calbright_email": calbright_email,
            "counselor_email": self.counselor_email,
            "email": email,
            "drop_program": program,
            "drop_reason": drop_reason,
            "email_prefix": email_prefix,
            "email_suffix": email_suffix,
        }
        self.device_email_sent = self.staff_email_sent = self.student_email_sent = False

        registrar = "registrar@calbright.org"
        admissions = "admissions@calbright.org"
        dev = "dev@calbright.org"
        enrollment = "enrollment@calbright.org"
        initiatives = "initiatives@calbright.org"
        learning = "learning@calbright.org"
        security = "security@calbright.org"

        self.staff_to = registrar
        self.device_bcc = [security]
        self.staff_bcc = [dev]
        self.staff_cc = [initiatives]
        self.student_bcc = [enrollment, initiatives]
        self.student_cc = [registrar, learning, self.counselor_email]

        self.salesforce_event = SalesforceEvent(
            configs={
                "constants": {
                    "email": {
                        "admissions": admissions,
                        "counselor": self.counselor_email,
                        "dev": dev,
                        "enrollment_services": enrollment,
                        "initiatives": initiatives,
                        "learning": learning,
                        "registrar": self.staff_to,
                        "security": security,
                    },
                    "link": {"catalog": "https://www.calbright.org/catalog"},
                },
                "feature_flags": {"castor": {"salesforce_event": {"active": True, "enabled": "ALL"}}},
            },
            calbright=calbright,
            gsuite_licensing=gsuite_licensing,
            gsuite_users=gsuite_users,
            hubspot=hubspot,
            salesforce=salesforce,
            strut=strut,
        )
        self.salesforce_event.is_student_processed = Mock(return_value=False)

    def test_required_fields(self):
        payload = {}
        for field in self.salesforce_event._required_fields:
            error_caught = False
            try:
                self.salesforce_event.run(payload)
            except MissingRequiredField as err:
                error_caught = True
                self.assertEqual(
                    str(err),
                    f'Event type "salesforce_event" is missing or size is 0 for the required field: {field}',
                )
            self.assertTrue(error_caught)
            payload[field] = field

        try:
            self.salesforce_event.check_required_fields(
                self.salesforce_event.__event_type__, payload, self.salesforce_event._required_fields
            )
            error_caught = False
        except MissingRequiredField:
            error_caught = True
        self.assertFalse(error_caught)

    def test_salesforce_events(self):
        self.test_name = "salesforce_event"
        self.salesforce_event.run(self.student_data)
        self.assertFalse(self.device_email_sent)
        self.assertTrue(self.staff_email_sent)
        self.assertTrue(self.student_email_sent)

        self.test_name = "salesforce_event_with_device"
        self.staff_email_sent = False
        self.student_email_sent = False
        self.student_data["Student__r"]["cfg_Chromebook_Requested__c"] = True
        self.salesforce_event.run(self.student_data)
        self.assertTrue(self.device_email_sent)
        self.assertTrue(self.staff_email_sent)
        self.assertTrue(self.student_email_sent)

        self.test_name = "salesforce_event_default_counselor"
        self.device_email_sent = False
        self.staff_email_sent = False
        self.student_email_sent = False
        self.salesforce_event.run(self.student_data)
        self.assertTrue(self.device_email_sent)
        self.assertTrue(self.staff_email_sent)
        self.assertTrue(self.student_email_sent)

    def send_transactional_email(self, email_id, to_email, cc=None, bcc=None, custom_properties=None):
        if email_id == AUTOMATIC_DROP_DEVICE:
            self.assertEqual(
                to_email, f'{custom_properties.get("name")} <{custom_properties.get("email")}>'
            )  # noqa: E501
            self.assertEqual(cc, [f'{custom_properties.get("name")} <{custom_properties.get("calbright_email")}>'])
            self.assertEqual(bcc, self.device_bcc)
            self.device_email_sent = True
        elif email_id == AUTOMATIC_DROP_STAFF:
            self.assertEqual(to_email, self.staff_to)
            self.assertEqual(cc, self.staff_cc)
            self.assertEqual(bcc, self.staff_bcc)
            self.staff_email_sent = True
        elif email_id == AUTOMATIC_DROP_STUDENT:
            self.assertEqual(to_email, f'{custom_properties.get("name")} <{custom_properties.get("email")}>')
            self.assertEqual(bcc, self.student_bcc)
            if self.test_name == "salesforce_event_default_counselor":
                self.assertEqual(cc, self.student_cc[:-1] + [self.counselor_email])
            else:
                self.assertEqual(cc, self.student_cc)
            self.student_email_sent = True


if __name__ == "__main__":
    unittest.main()
