from datetime import datetime
from zoneinfo import ZoneInfo
from typing import AnyStr, Dict, List

from propus import Logging


class SalesforceService:
    def __init__(self, client):
        self.logger = Logging.get_logger("services/salesforce_service.py")
        self.client = client

    def update_tdd(self, tdd_label: AnyStr) -> None:
        """
        This function is primarily used for test driven development. It updates the salesforce client with
        a tdd flag. This should only be used for development and within our Mock Salesforce class. If used
        in production it will break.

        Args:
            tdd_label (AnyStr): label of the test driven development case that is being tested
        """
        self.logger.debug(f"setting tdd_case {tdd_label}")
        self.client.tdd_case = tdd_label

    def fetch_bulk_contact_data(self, ccc_ids: List) -> Dict:
        """
        This function takes in a list of CCCIDs and queries salesforce for contact record information. It logs an error
        and returns None if no student was found with this CCCID.
        Args:
            ccc_id (List): list of strings of the student ccc_ids
        Returns:
            Dict: Dictionary of contact record data from salesforce with the id (Salesforce ID), first_name (Student's
                First Name), last_name (Student's Last Name), email (Student's Calbright Email), enrollment_date(
                Student's Enrollment Date), learner_status (Student's Learner Status), and academic_counselor_email(
                Student's Academic Counselor Email)
        """
        response = self.client.custom_query(
            f"""SELECT Id, FirstName, LastName, Date_of_Enrollment__c, cfg_Calbright_Email__c, cfg_Learner_Status__c,
            cfg_Intended_Program__c, Assigned_Academic_Counselor_Email__c, cfg_CCC_ID__c FROM
            Contact WHERE cfg_CCC_ID__c IN ('{"', '".join(ccc_ids)}') AND cfg_Learner_Status__c IN
            ('Started Program Pathway', 'Enrolled in Program Pathway')"""
        )

        contact_data = {}
        for record in response.get("records"):
            enrollment_date = None
            if record.get("Date_of_Enrollment__c") is not None:
                enrollment_date_utc = datetime.strptime(record.get("Date_of_Enrollment__c"), "%Y-%m-%dT%H:%M:%S.000%z")
                enrollment_date_pst = enrollment_date_utc.astimezone(ZoneInfo("America/Los_Angeles"))
                enrollment_date = datetime(
                    enrollment_date_pst.year,
                    enrollment_date_pst.month,
                    enrollment_date_pst.day,
                    tzinfo=ZoneInfo("America/Los_Angeles"),
                )
            contact_data[record.get("cfg_CCC_ID__c")] = {
                "id": record.get("Id"),
                "first_name": record.get("FirstName"),
                "last_name": record.get("LastName"),
                "email": record.get("cfg_Calbright_Email__c"),
                "enrollment_date": enrollment_date,
                "learner_status": record.get("cfg_Learner_Status__c"),
                "academic_counselor_email": record.get("Assigned_Academic_Counselor_Email__c"),
                "program": record.get("cfg_Intended_Program__c"),
            }
        self.logger.info(f"Salesforce: Found {len(contact_data)} of {len(ccc_ids)} contacts")
        return contact_data

    def fetch_trailhead_user_data(self, sf_id: AnyStr) -> AnyStr:
        """
        This function queries salesforce User record by salesforce contact record id

        Args:
            sf_id (AnyStr): Contact Record ID

        Returns:
            AnyStr: The user ID found
        """
        response = self.client.custom_query(f"SELECT Id FROM User WHERE ContactId = '{sf_id}'")
        if not response.get("totalSize"):
            self.logger.error(f"fetch_trailhead_user_data: no matching user record for ccc_id {sf_id}")
            return None
        return response.get("records")[0].get("Id")

    def fetch_user_badges(self, user_id: AnyStr) -> Dict:
        """
        This function queries salesforce using the Salesforce User Id to retrieve the user's completed
        badges and the associated completion date in UTC

        Args:
            user_id (AnyStr): Student's Salesforce User Record Id

        Returns:
            List: List of dictionary responses of badge and completion datetimes
                - badge_name: name of badge compelted
                - completion_datetime: datetime (in UTC) of when the badge was completed
        """
        response = self.client.custom_query(
            f"""SELECT trailheadapp__Badge__r.Name, trailheadapp__Last_Attempted_Date__c FROM
            trailheadapp__User_Badge__c WHERE trailheadapp__User__c = '{user_id}' AND
            trailheadapp__Status__c = 'Completed'"""
        )
        return [
            {
                "badge_name": record.get("trailheadapp__Badge__r").get("Name"),
                "completion_datetime": datetime.strptime(
                    record.get("trailheadapp__Last_Attempted_Date__c"), "%Y-%m-%dT%H:%M:%S.000%z"
                ),
            }
            for record in response.get("records", [])
        ]
