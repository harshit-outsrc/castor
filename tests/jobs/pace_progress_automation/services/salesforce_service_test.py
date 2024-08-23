from datetime import datetime
from dateutil import tz
import unittest
from unittest.mock import MagicMock, Mock

from jobs.pace_progress_automation.services.salesforce_service import SalesforceService


class TestSalesforceService(unittest.TestCase):
    def setUp(self) -> None:
        sf_client = MagicMock()
        sf_client.tdd_case = None
        sf_client.custom_query = Mock(side_effect=self.custom_query)
        self.salesforce = SalesforceService(sf_client)
        self.contact = {
            "Id": "AJNKFDJKBK1234",
            "FirstName": "Jane",
            "LastName": "Doe",
            "cfg_Calbright_Email__c": "you@me.com",
            "Date_of_Enrollment__c": "2022-01-03T00:12:34.000+0000",
            "cfg_Learner_Status__c": "Excelling!",
            "Assigned_Academic_Counselor_Email__c": "asc@calbright.org",
            "cfg_CCC_ID__c": "ABSD1234JKNSD",
        }
        self.trailhead = {"Id": "TRAILHEAD_#$XYZ"}
        self.badge_names = ["badge_1", "badge_2"]
        self.created_dates = ["2023-03-01T12:34:12.000+0000", "2023-04-03T06:22:18.000+0000"]
        self.badges = [
            {
                "trailheadapp__Badge__r": {"Name": self.badge_names[i]},
                "trailheadapp__Last_Attempted_Date__c": self.created_dates[i],
            }
            for i in range(len(self.badge_names))
        ]
        self.test_data = {
            "ccc_id": "ABC1234",
            "sf_id": "AHJKFJDDF781293789",
            "contact_data": {
                "totalSize": 1,
                "records": [],
            },
        }
        self.test_name = None

    def test_update_tdd(self):
        test_tdd_label = "TEST_LABEL"
        self.salesforce.update_tdd(test_tdd_label)
        self.assertEqual(test_tdd_label, self.salesforce.client.tdd_case)

    def test_fetch_contact_data(self):
        self.test_name = "successful_contact_query"
        response = self.salesforce.fetch_bulk_contact_data([self.test_data.get("ccc_id")])
        contact_response = response.get(self.contact.get("cfg_CCC_ID__c"))
        self.assertEqual(self.contact.get("Id"), contact_response.get("id"))
        self.assertEqual(self.contact.get("FirstName"), contact_response.get("first_name"))
        self.assertEqual(self.contact.get("LastName"), contact_response.get("last_name"))
        self.assertEqual(self.contact.get("cfg_Calbright_Email__c"), contact_response.get("email"))
        self.assertEqual(self.contact.get("cfg_Learner_Status__c"), contact_response.get("learner_status"))
        self.assertEqual(
            self.contact.get("Assigned_Academic_Counselor_Email__c"),
            contact_response.get("academic_counselor_email"),
        )

    def test_fetch_trailhead_user_data(self):
        self.test_name = "no_trailhead_user_found"
        self.assertIsNone(self.salesforce.fetch_trailhead_user_data(self.test_data.get("sf_id")))

        self.test_name = "trailhead_user_found_success"
        trailhead_id = self.salesforce.fetch_trailhead_user_data(self.test_data.get("sf_id"))
        self.assertEqual(trailhead_id, self.trailhead.get("Id"))

    def test_fetch_user_badges(self):
        self.test_name = "badge_query"
        badges = self.salesforce.fetch_user_badges(self.test_data.get("sf_id"))
        comp_dates = [
            datetime(2023, 3, 1, 12, 34, 12, tzinfo=tz.gettz("UTC")),
            datetime(2023, 4, 3, 6, 22, 18, tzinfo=tz.gettz("UTC")),
        ]
        for badge in badges:
            self.assertIn(badge.get("badge_name"), self.badge_names)
            self.assertIn(badge.get("completion_datetime"), comp_dates)

    def custom_query(self, query):
        if self.test_name == "successful_contact_query":
            self.assertEqual(
                query,
                """SELECT Id, FirstName, LastName, Date_of_Enrollment__c, cfg_Calbright_Email__c, cfg_Learner_Status__c,
            cfg_Intended_Program__c, Assigned_Academic_Counselor_Email__c, cfg_CCC_ID__c FROM
            Contact WHERE cfg_CCC_ID__c IN ('ABC1234') AND cfg_Learner_Status__c IN
            ('Started Program Pathway', 'Enrolled in Program Pathway')""",
            )
            if self.test_name == "successful_contact_query":
                self.test_data["records"] = [self.contact]
                self.test_data["totalSize"] = 1
                return self.test_data
        elif self.test_name in ["no_trailhead_user_found", "trailhead_user_found_success"]:
            self.assertEqual(query, "SELECT Id FROM User WHERE ContactId = 'AHJKFJDDF781293789'")
            if self.test_name == "trailhead_user_found_success":
                self.test_data["records"] = [self.trailhead]
                self.test_data["totalSize"] = 1
                return self.test_data
        else:
            self.assertEqual(
                query,
                """SELECT trailheadapp__Badge__r.Name, trailheadapp__Last_Attempted_Date__c FROM
            trailheadapp__User_Badge__c WHERE trailheadapp__User__c = 'AHJKFJDDF781293789' AND
            trailheadapp__Status__c = 'Completed'""",
            )
            self.test_data["records"] = self.badges
            return self.test_data

        return {"totalSize": 0}


if __name__ == "__main__":
    unittest.main()
