import unittest
from unittest.mock import MagicMock, Mock

from lambda_functions.event_system.events.dpau_complete import DPAUComplete


class TestEventDPAUComplete(unittest.TestCase):

    def setUp(self):
        self.salesforce = MagicMock()
        self.salesforce.get_student_devices_by_ccc_id = Mock(side_effect=self.get_student_devices_by_ccc_id)
        self.salesforce.client.update_contact_record = Mock(side_effect=self.update_contact_record)

        self.sqs = MagicMock()
        self.sqs.send_message.return_value = True

        self.geolocator = MagicMock()
        self.geolocator.get = Mock(side_effect=self.get_shipping_address)

        self.dpau_complete = DPAUComplete(
            configs={},
            salesforce=self.salesforce,
            geolocator=self.geolocator,
            sqs=self.sqs,
        )

        self.test_event_data = {
            "date_modified": "2024-06-17T03:23:45",
            "shipping_address": "1102 Q St. Suite 4800, Sacramento, CA 95811",
            "tokens": [
                {"Student.CalbrightEmail": "testing@testington.test"},
                {"Student.CCCID": "TEST123"},
                {"Student.FullName": "Test TestingTon"},
            ],
            "fields": [
                {"field_id": "ShippingAddress", "value": "1102 Q St. Suite 4800, Sacramento, CA 95811"},
                {"field_id": "chromebook_checked", "value": True},
                {"field_id": "hotspot_checked", "value": False},
            ],
            "id": "some_id",
            "recipients": [{"shared_link": "HTTPS://LINK.ME"}],
        }

        self.test_salesforce_record = {
            "Id": "123testingsalesforceid",
            "FirstName": "Test",
            "LastName": "TestingTon",
            "Device_Requested_On_CSEP__C": False,
            "Device_Agreement_Sent_For_Signature_Date__C": "2024-06-16T03:23:45",
            "Device_Shipping_Address__C": "1102 Q St. Suite 4800, Sacramento, CA 95811",
            "Email": "testing@nonstudent.test",
            "Name": "Test TestingTon",
            "Phone": "1234567890",
            "cfg_Calbright_Email__c": "testing@testington.test",
            "cfg_Chromebook_Requested__c": False,
            "cfg_Hotspot_Requested__c": False,
        }

        self.updated_salesforce = False

    def test_run(self):
        self.dpau_complete.run(self.test_event_data)
        self.assertTrue(self.updated_salesforce)
        self.sqs.send_message.assert_called_once()

    def test_validate_dpau_data(self):
        valid_tokens = self.test_event_data.get("tokens")
        self.dpau_complete.validate_dpau_data({"tokens": valid_tokens})
        student_tokens, student_record = self.dpau_complete.validate_dpau_data({"tokens": valid_tokens})
        self.assertEqual(student_record, self.test_salesforce_record)
        self.assertEqual(
            student_tokens.get("Student.CCCID"), self.test_event_data.get("tokens")[1].get("Student.CCCID")
        )

    def test_get_dpau_requests(self):
        event_data = {
            "fields": [
                {"field_id": "chromebook_checked", "value": True},
                {"field_id": "hotspot_checked", "value": False},
                {"field_id": "ShippingAddress", "value": "1102 Q St. Suite 4800, Sacramento, CA 95811"},
            ]
        }
        expected_output = {
            "chromebook": True,
            "hotspot": False,
            "shipping_address": "1102 Q St. Suite 4800, Sacramento, CA 95811",
        }
        self.assertEqual(self.dpau_complete.get_dpau_requests(event_data), expected_output)

    def get_shipping_address(self, location):
        expected_output = {
            "address1": "1102 Q St.",
            "address2": "Suite 4800",
            "city": "Sacramento",
            "state": "CA",
            "zip": "95811",
            "country": "US",
        }
        self.assertEqual(
            location,
            f'{expected_output.get("address1")} {expected_output.get("address2")}, {expected_output.get("city")}, {expected_output.get("state")} {expected_output.get("zip")}',  # noqa: E501
        )
        return expected_output

    def get_student_devices_by_ccc_id(self, ccc_id):
        self.assertEqual(ccc_id, self.test_event_data.get("tokens")[1].get("Student.CCCID"))
        return self.test_salesforce_record

    def update_contact_record(self, salesforce_id, **kwargs):
        self.updated_salesforce = True
        self.assertEqual(salesforce_id, self.test_salesforce_record.get("Id"))
        self.assertEqual(
            kwargs,
            {
                "Device_Agreement_Signed_Date__c": self.test_event_data.get("date_modified"),
                "Device_Shipping_Address__c": self.test_event_data.get("shipping_address"),
            },
        )


if __name__ == "__main__":
    unittest.main()
