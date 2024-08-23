from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock

SF_DT = "%Y-%m-%dT%H:%M:%S.000+0000"
NOW = datetime.now()


class MockSalesforce:
    def __init__(self):
        from mock_classes.badge_responses import (
            fetch_ontrack_badges,
            fetch_ahead_badges,
            fetch_behind_badges,
        )

        sf = MagicMock()
        sf.custom_query = Mock(side_effect=self.custom_query)

        self.client = sf
        self.tdd_case = None

        self.enrollment_date_dict = {
            "not_correct_day": (NOW - timedelta(days=12)).strftime(SF_DT),
            "enrolled_yesterday": (NOW - timedelta(days=1)).strftime(SF_DT),
            "1_week": (NOW - timedelta(days=7)).strftime(SF_DT),
            "2_week": (NOW - timedelta(days=2 * 7)).strftime(SF_DT),
            "5_week": (NOW - timedelta(days=5 * 7)).strftime(SF_DT),
            "6_week": (NOW - timedelta(days=6 * 7)).strftime(SF_DT),
            "7_week": (NOW - timedelta(days=7 * 7)).strftime(SF_DT),
        }

        self.contact_record_data = {
            "totalSize": 1,
            "records": [
                {
                    "Id": "ContactABC",
                    "Date_of_Enrollment__c": None,
                    "FirstName": "Jane",
                    "LastName": "Doe",
                    "cfg_Calbright_Email__c": "brendan.volheim@calbright.org",
                    "cfg_Learner_Status__c": "Started Program Pathway",
                    "Assigned_Academic_Counselor_Email__c": "test_asc@calbright.org",
                }
            ],
        }

        self.user_record_data = {
            "totalSize": 1,
            "records": [{"Id": "UserABC"}],
        }

        self.badge_responses = {
            "1_week_on_track_90_Day": fetch_ontrack_badges("90 Day", 1),
            "2_week_1_gp_on_track_90_Day": fetch_ontrack_badges("90 Day", 1),
            "2_week_on_track_90_Day": fetch_ontrack_badges("90 Day", 2),
            "1_week_behind_90_Day": fetch_behind_badges("90 Day", 1),
            "2_week_behind_90_Day": fetch_behind_badges("90 Day", 2),
            "1_week_on_track_120_Day": fetch_ontrack_badges("120 Day", 1),
            "1_week_on_track_180_Day": fetch_ontrack_badges("180 Day", 1),
            "1_week_on_track_365_Day": fetch_ontrack_badges("365 Day", 1),
            "1_week_ahead_90_Day": fetch_ahead_badges("90 Day", 1),
            "5_week_behind_90_Day": fetch_behind_badges("90 Day", 1),
            "6_week_behind_90_Day": fetch_behind_badges("90 Day", 1),
            "7_week_behind_90_Day": fetch_behind_badges("90 Day", 1),
        }

    def custom_query(self, query):
        if "SELECT Id, FirstName, LastName, Date_of_Enrollment__c, cfg_Calbright_Email__c" in query:
            if "enrolled_yesterday" in self.tdd_case:
                date = self.enrollment_date_dict.get("enrolled_yesterday")
            elif "not_correct_day" in self.tdd_case:
                date = self.enrollment_date_dict.get("not_correct_day")
            elif "_week_" in self.tdd_case:
                week_key = self.tdd_case[: self.tdd_case.index("_week_")] + "_week"
                date = self.enrollment_date_dict.get(week_key)
            self.contact_record_data.get("records")[0]["Date_of_Enrollment__c"] = date
            status = "Started Program Pathway"
            if "epp_status" in self.tdd_case:
                status = "Enrolled in Program Pathway"
            self.contact_record_data.get("records")[0]["cfg_Learner_Status__c"] = status
            return self.contact_record_data
        elif query == "SELECT Id FROM User WHERE ContactId = 'ContactABC'":
            return self.user_record_data
        elif "trailheadapp__Badge__r.Name" in query:
            return self.badge_responses.get(self.tdd_case)
