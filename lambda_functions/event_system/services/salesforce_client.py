from datetime import timedelta, datetime
from services.base_client import fetch_ssm
from exceptions import CccIdNotInSalesforce, MultipleCccIdInSalesforce, EmailNotInSalesforce
from propus.salesforce import Salesforce
from propus.helpers.sql_alchemy import build_query
from propus.logging_utility import Logging


CALENDLY_INTAKE_ROLES = ("counselor", "student support")


class SalesforceClient:
    _client = None

    def __new__(cls, param_name, ssm):
        if cls._client is None:
            cls._client = Salesforce.build(**fetch_ssm(ssm, param_name, True))

        return cls._client


class SalesforceService:
    def __init__(self, param_name, ssm):
        self.client = SalesforceClient(param_name, ssm)
        self.logger = Logging.get_logger("castor/lambda_functions/event_system/services/salesforce_client")

    def get_learner_status_by_email(self, email):
        records = self.client.custom_query(
            f"""Select Id, Cfg_CCC_ID__c, Cfg_Learner_Status__c FROM contact WHERE Email = '{email}'
                OR cfg_Calbright_Email__c = '{email}'"""
        ).get("records")

        return records[0].get("cfg_CCC_ID__c"), records[0].get("cfg_Learner_Status__c")

    def get_next_term(self, start_date: str):
        start_datetime = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S.%fZ")
        week_later = start_datetime + timedelta(days=7)
        records = self.client.custom_query(
            f"""SELECT id, Name FROM hed__Term__c WHERE hed__Start_Date__c >= {start_datetime.strftime('%Y-%m-%d')} AND
            hed__Start_Date__c < {week_later.strftime('%Y-%m-%d')} ORDER BY hed__Start_Date__c LIMIT 1"""
        )
        if not records.get("totalSize"):
            raise Exception(f"No Term found with start date after {start_datetime.strftime('%Y-%m-%d')}")
        return records.get("records")[0]

    def get_user_record(self, id):
        records = self.client.custom_query(f"""Select Id, FROM user WHERE id = '{id}'""").get("records")

        return records[0].get("Id")

    def get_user_by_id(self, id):
        records = self.client.custom_query(f"""Select Id, Name, Email FROM user WHERE id = '{id}'""").get("records")

        return records[0]

    def get_student_salesforce_fields(self, ccc_id):
        fields = [
            "(Select Id From Veteran_Service_Records__r)",
            "cfg_Assigned_Learner_Advocate__r.Id",
            "cfg_Assigned_Learner_Advocate__r.Name",
            "cfg_Assigned_Learner_Advocate__r.Email",
            "cfg_Assigned_Learner_Advocate__r.Strut_User_ID__c",
            "cfg_Intended_Program__C",
            "Device_Agreement_Sent_For_Signature_Date__C",
            "customer_community_user_created__c",
        ]
        records = self.client.custom_query(build_query("Contact", fields, [f"cfg_CCC_ID__c = '{ccc_id}'"]))
        if records.get("totalSize") == 0:
            self.logger.error(f"ccc_id {ccc_id} not in salesforce")
            raise CccIdNotInSalesforce(ccc_id)

        if records.get("totalSize") > 1:
            self.logger.error(f"multiple records were found for ccc_id {ccc_id} in salesforce")
            raise MultipleCccIdInSalesforce(ccc_id)
        record = records.get("records").pop()
        record["ccc_id"] = ccc_id
        return record

    def get_student_devices_by_ccc_id(self, ccc_id):
        fields = [
            "Id",
            "FirstName",
            "LastName",
            "cfg_Intended_Program__C",
            "Device_Requested_On_CSEP__C",
            "Device_Agreement_Sent_For_Signature_Date__C",
            "Device_Shipping_Address__C",
            "Email",
            "Name",
            "Phone",
            "cfg_Learner_Status__c",
            "cfg_Calbright_Email__c",
            "cfg_Chromebook_Requested__c",
            "cfg_Hotspot_Requested__c",
        ]
        records = self.client.custom_query(build_query("Contact", fields, [f"cfg_CCC_ID__c = '{ccc_id}'"]))
        if records.get("totalSize") == 0:
            self.logger.error(f"ccc_id {ccc_id} not in salesforce")
            raise CccIdNotInSalesforce(ccc_id)

        if records.get("totalSize") > 1:
            self.logger.error(f"multiple records were found for ccc_id {ccc_id} in salesforce")
            raise MultipleCccIdInSalesforce(ccc_id)

        return records.get("records").pop()

    def get_program_enrollments_in_progress(self, contact_id, program_name):
        return self.client.custom_query(
            f"""
            SELECT id, Program_Name__c, Program_Version__c, Enrollment_Status__c, Enrollment_Status_Date__c, Contact__c
            FROM Program_Enrollments__c  WHERE Contact__r.id = '{contact_id}' AND Program_Name__c = '{program_name}' AND
            Enrollment_Status__c = 'In Progress'
            """
        ).get("records")

    def get_trailmix_assignments(self, contact_id):
        return self.client.custom_query(
            f"""
            SELECT Id, Contact__c, cc_Progress__c,
            trailheadapp__Trailmix__c FROM
            trailheadapp__Trailmix_Assignment__c WHERE
            Contact__r.id = '{contact_id}'
            """
        ).get("records")

    def get_contact_ids_by_email(self, user_email: str) -> list:
        """
        Look up records by email (calbright or personal email).

            Args:
                user_email (str): Email of user in Salesforce

            Returns:
                records (list): A list of records with user IDs

        """
        records = self.client.custom_query(
            f"""Select Id FROM contact WHERE Email = '{user_email}'
            OR cfg_Calbright_Email__c = '{user_email}'"""
        )

        return records

    def get_contact_by_email(self, user_email):
        records = self.client.custom_query(
            f"""Select Id, FirstName, LastName, cfg_Learner_Status__c,
            cfg_Intended_Program__c, Email, Phone,
            cfg_Programs_of_Interest__c FROM
            contact WHERE Email = '{user_email}'
            OR cfg_Calbright_Email__c = '{user_email}'"""
        ).get("records")

        if not records:
            raise EmailNotInSalesforce(user_email)

        return records[0]

    def get_calbright_user_by_email(self, user_email: str) -> dict:
        """
        Retrieve first Calbright user information found based on user email,
        if the user title is 'counselor' or 'student support'

            Args:
                user_email (str): Email of user in Salesforce

            Returns:
                user_info (dict): user information with "Id" and "Title" keys, if 'counselor' or 'student support'
                None: if user title not in 'counselor' or 'student support'

        """
        if user_email:
            response = self.client.custom_query(f"SELECT Id, Title, Email FROM User WHERE Email = '{user_email}'")
            for attendee in response.get("records", []):
                title = attendee.get("Title", "")
                if title and title.lower() in CALENDLY_INTAKE_ROLES:
                    return attendee.get("Id")

        return None
