import unittest
from typing import AnyStr, Dict
from unittest.mock import MagicMock, Mock

from lambda_functions.event_system.events.dpau_request import DPAURequest


class TestEventDPAURequest(unittest.TestCase):
    def setUp(self):
        salesforce = MagicMock()
        salesforce.get_student_devices_by_ccc_id = Mock(side_effect=self.get_student_devices_by_ccc_id)
        salesforce.client.update_contact_record = Mock(side_effect=self.update_contact_record)

        sqs = MagicMock()
        sqs.send_message = Mock(side_effect=self.send_to_tangoe_event)

        self.dpau_request = DPAURequest(
            configs={},
            salesforce=salesforce,
            pandadoc=MagicMock(),
            geolocator=MagicMock(),
            slack=MagicMock(),
            sqs=sqs,
        )

        self.sent_to_tangoe_event = False
        self.panda_doc_sent = False
        self.student_updated = False

        self.test_data = {
            "form_id": "123123123123",
            "response_id": "09988098098",
            "dpau_form_submitted": "2024-05-24T12:34:56",
            "ccc_id": "TST1234",
            "calbright_email": "testington@test.com",
            "chromebook": "Yes",
            "hotspot": "No",
            "street": "123 Test st",
            "city": "TestingTon",
            "state": "TS",
            "zipcode": "12345",
            "event_timestamp": "2024-05-24T12:34:56",
        }

        self.salesforce_data = {
            "Device_Requested_on_CSEP__c": True,
            "Device_Agreement_Signed_Date__c": "2024-05-24T12:34:56",
            "FirstName": "Test",
            "LastName": "Testing",
            "Phone": "123456789",
            "Id": "TotallyLegitSalesforceID",
            "cfg_Calbright_Email__c": "testington@test.com",
        }

    def test_device_request_from_post_csep(self):
        self.dpau_request.run(self.test_data)
        self.assertTrue(self.sent_to_tangoe_event)
        self.assertFalse(self.student_updated)

        self.sent_to_tangoe_event = False
        self.salesforce_data["Device_Requested_on_CSEP__c"] = False
        self.salesforce_data["Device_Agreement_Signed_Date__c"] = None
        self.dpau_request.run(self.test_data)
        self.assertFalse(self.sent_to_tangoe_event)
        self.assertTrue(self.student_updated)

    def get_student_devices_by_ccc_id(self, ccc_id):
        return self.salesforce_data

    def update_contact_record(self, salesforce_id, **kwargs):
        self.student_updated = True
        return

    def send_to_tangoe_event(self, queue_name: AnyStr, message: AnyStr, message_attributes: Dict = {}, **kwargs):
        self.sent_to_tangoe_event = True
        return


if __name__ == "__main__":
    unittest.main()
