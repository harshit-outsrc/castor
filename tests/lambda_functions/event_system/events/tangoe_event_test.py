import unittest
from unittest.mock import MagicMock, Mock

from lambda_functions.event_system.events.tangoe_event import TangoeEvent


class TestEventTangoeEvent(unittest.TestCase):
    def setUp(self):
        salesforce = MagicMock()
        salesforce.get_student_devices_by_ccc_id = Mock(side_effect=self.get_student_devices_by_ccc_id)
        salesforce.client.update_contact_record = Mock(side_effect=self.update_contact_record)

        self.tangoe_event = TangoeEvent(
            salesforce=salesforce,
            gsheets=MagicMock(),
            slack=MagicMock(),
            geolocator=MagicMock(),
            tangoemobile=MagicMock(),
            tangoepeople=MagicMock(),
        )

        self.grabbed_current_devices = False
        self.student_updated = False

        self.test_data = {
            "student_info": {
                "id": "123",
                "city": "Sac",
                "state": "CA",
                "street": "123 st",
                "zipcode": "95811",
                "device_requested_method": "CSEP",
                "device_agreement_sent_for_signature": True,
                "first_name": "fname",
                "last_name": "lname",
                "ccc_id": "TST1111",
                "email": "testing@calbrightcollege.org",
                "phone": "1234567890",
                "policy_signed": True,
                "cb_requested": True,
                "hs_requested": True,
            },
            "event_timestamp": "2023-06-24T12:34:56",
        }

    def test_device_request_from_csep(self):
        self.tangoe_event.run(self.test_data)
        self.assertTrue(self.grabbed_current_devices)
        self.assertTrue(self.student_updated)

    def get_student_devices_by_ccc_id(self, ccc_id):
        self.grabbed_current_devices = True
        return {"cfg_Chromebook_Requested__c": False, "cfg_Hotspot_Requested__c": False}

    def update_contact_record(self, salesforce_id, **kwargs):
        self.student_updated = True

    def test_device_return(self):
        self.test_data['student_info']['cb_requested'] = False
        self.test_data['student_info']['hs_requested'] = False
        self.test_data['student_info']['cb_return'] = True
        self.test_data['student_info']['hs_return'] = True
        self.tangoe_event.run(self.test_data)
        self.assertTrue(self.grabbed_current_devices)
        self.assertTrue(self.student_updated)


if __name__ == "__main__":
    unittest.main()
