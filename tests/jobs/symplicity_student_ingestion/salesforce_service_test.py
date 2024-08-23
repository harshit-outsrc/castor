import unittest
from unittest.mock import MagicMock, Mock

from jobs.symplicity_student_ingestion.salesforce_service import SalesforceService, fetch_csm_picklist_data


class TestSalesforceService(unittest.TestCase):
    def setUp(self) -> None:
        self.csm_keys = {
            "current_status": {"Current Student": "1", "Alumni": "2"},
            "learner_status": {"Started Program Pathway": "14", "Completed Program Pathway": "13"},
            "intended_program": {"T2T CRM Admin": "0060", "HC DEI": "0080", "T2T Intro to Networks": "0200"},
            "programs_complete": {
                "Customer Relationship Management": "0060",
                "HC DEI": "0080",
                "T2T Intro to Networks": "0200",
            },
            "counselors": {"shemila@calbright.org": "1234"},
        }
        sf_client = MagicMock()
        sf_client.bulk_custom_query_operation = Mock(side_effect=self.bulk_custom_query_operation)
        self.sf_query_count = 0
        self.salesforce_service = SalesforceService(sf_client, self.csm_keys)

        self.current_student = {
            "cfg_CCC_ID__c": "CURRENT_STUDENT",
            "cfg_Calbright_Email__c": "John.Doe@calbright.org",
            "FirstName": "Legend",
            "LastName": "Doe",
            "cfg_Full_Name__c": "John Doe",
            "Chosen_First_Name__c": "Legend",
            "Chosen_Last_Name__c": "Doe",
            "Email": "jd@gmail.com",
            "cfg_Intended_Program__c": "T2T CRM Admin",
            "cfg_Learner_Status__c": "Started Program Pathway",
            "Date_of_Enrollment__c": "2023-04-25T23:35:48.000Z",
            "Current_Term_End_Date_c__c": "2024-04-22",
            "MailingStreet": "123 Main Street",
            "MailingCity": "Mill Valley",
            "MailingPostalCode": "94941",
            "Phone": "(123) 345-6780",
            "MobilePhone": "(987) 765-4321",
            "Leave_Start_Date__c": "2024-02-02",
            "Leave_End_Date__c": "2024-05-01",
            "HasOptedOutOfEmail": "false",
            "SMS_Opt_Out__c": "false",
            "DoNotCall": "false",
            "Assigned_Academic_Counselor_Email__c": "shemila@calbright.org",
            "Legal_First_Name__c": "John",
        }

        self.alumni_students = [
            {
                "Contact__r.cfg_CCC_ID__c": "ALUMNI",
                "Contact__r.cfg_Calbright_Email__c": "John.Doe@calbright.org",
                "Contact__r.FirstName": "Legend",
                "Contact__r.LastName": "Doe",
                "Contact__r.cfg_Full_Name__c": "John Doe",
                "Contact__r.Chosen_First_Name__c": "Legend",
                "Contact__r.Chosen_Last_Name__c": "Doe",
                "Contact__r.Email": "jd@gmail.com",
                "Contact__r.cfg_Intended_Program__c": "T2T CRM Admin",
                "Contact__r.cfg_Learner_Status__c": "Completed Program Pathway",
                "Contact__r.Date_of_Enrollment__c": "2023-04-25T23:35:48.000Z",
                "Contact__r.Current_Term_End_Date_c__c": "2024-04-22",
                "Contact__r.MailingStreet": "123 Main Street",
                "Contact__r.MailingCity": "Mill Valley",
                "Contact__r.MailingPostalCode": "94941",
                "Contact__r.Phone": "(123) 345-6780",
                "Contact__r.MobilePhone": "(987) 765-4321",
                "Contact__r.Leave_Start_Date__c": "2024-02-02",
                "Contact__r.Leave_End_Date__c": "2024-05-01",
                "Contact__r.HasOptedOutOfEmail": "false",
                "Contact__r.SMS_Opt_Out__c": "false",
                "Contact__r.DoNotCall": "false",
                "Contact__r.Assigned_Academic_Counselor_Email__c": "shemila@calbright.org",
                "Contact__r.Legal_First_Name__c": "John",
                "Enrollment_Status_Date__c": "2023-08-17T18:06:53.000Z",
                "Program_Name__c": "T2T Intro to Networks",
            },
            {
                "Contact__r.cfg_CCC_ID__c": "ALUMNI",
                "Contact__r.cfg_Calbright_Email__c": "John.Doe@calbright.org",
                "Contact__r.FirstName": "Legend",
                "Contact__r.LastName": "Doe",
                "Contact__r.cfg_Full_Name__c": "John Doe",
                "Contact__r.Chosen_First_Name__c": "Legend",
                "Contact__r.Chosen_Last_Name__c": "Doe",
                "Contact__r.Email": "jd@gmail.com",
                "Contact__r.cfg_Intended_Program__c": "T2T CRM Admin",
                "Contact__r.cfg_Learner_Status__c": "Completed Program Pathway",
                "Contact__r.Date_of_Enrollment__c": "2023-04-25T23:35:48.000Z",
                "Contact__r.Current_Term_End_Date_c__c": "2024-04-22",
                "Contact__r.MailingStreet": "123 Main Street",
                "Contact__r.MailingCity": "Mill Valley",
                "Contact__r.MailingPostalCode": "94941",
                "Contact__r.Phone": "(123) 345-6780",
                "Contact__r.MobilePhone": "(987) 765-4321",
                "Contact__r.Leave_Start_Date__c": "2024-02-02",
                "Contact__r.Leave_End_Date__c": "2024-05-01",
                "Contact__r.HasOptedOutOfEmail": "false",
                "Contact__r.SMS_Opt_Out__c": "false",
                "Contact__r.DoNotCall": "false",
                "Contact__r.Assigned_Academic_Counselor_Email__c": "shemila@calbright.org",
                "Contact__r.Legal_First_Name__c": "John",
                "Enrollment_Status_Date__c": "2023-08-17T18:06:53.000Z",
                "Program_Name__c": "Customer Relationship Management",
            },
        ]

    def test_fetch_csm_picklist_data(self):
        csm = MagicMock()
        csm.fetch_form_picklist = Mock(side_effect=self.fetch_form_picklist)
        resp = fetch_csm_picklist_data(csm)
        self.assertEqual(resp.get("current_status"), self.csm_keys.get("current_status"))
        self.assertEqual(resp.get("learner_status"), self.csm_keys.get("learner_status"))
        self.assertEqual(resp.get("intended_program"), self.csm_keys.get("intended_program"))
        self.assertEqual(resp.get("programs_complete"), self.csm_keys.get("programs_complete"))

    def fetch_form_picklist(self, form_name):
        program_data = [
            {"id": "0060", "value": "Transition to Technology: CRM Platform Administration"},
            {"id": "0080", "value": "Upskilling to Equitable Health Impact: Diversity, Equity, and Inclusion"},
            {"id": "0200", "value": "Transition To Technology: Introduction to Networks"},
        ]
        form_data = {
            "applicantType": [{"id": "1", "value": "Current Student"}, {"id": "2", "value": "Alumni"}],
            "enrollment_status": [
                {"id": "14", "value": "Started Program Pathway"},
                {"id": "13", "value": "Completed Program Pathway"},
            ],
            "majors": program_data,
            "calbright_programs_completed": program_data,
        }
        return form_data.get(form_name)

    def test_fetch_csm_eligible_students(self):
        resp = self.salesforce_service.fetch_csm_eligible_students()
        self.assertEqual(len(resp), 2)
        for ccc_id, data in resp.items():
            self.assertEqual(data.get("schoolStudentId"), ccc_id)
            self.assertEqual(data.get("email"), "John.Doe@calbright.org")
            self.assertEqual(data.get("firstName"), "John")
            self.assertEqual(data.get("lastName"), "Doe")
            self.assertEqual(data.get("fullName"), "John Doe")
            self.assertEqual(data.get("permanentEmail"), "jd@gmail.com")
            self.assertEqual(data.get("majors"), ["0060"])
            self.assertEqual(data.get("date_of_enrollment"), "2023-04-25")
            self.assertEqual(data.get("current_end_term_date"), "2024-04-22")
            self.assertEqual(data.get("phone"), "(123) 345-6780")
            self.assertEqual(data.get("mobile_phone_number"), "(987) 765-4321")
            self.assertEqual(data.get("leave_start_date"), "2024-02-02")
            self.assertEqual(data.get("leave_end_date"), "2024-05-01")
            self.assertEqual(data.get("email_opt_out"), False)
            self.assertEqual(data.get("sms_opt_out"), False)
            self.assertEqual(data.get("do_not_call"), False)
            self.assertEqual(data.get("counselors"), ["1234"])
            self.assertEqual(data.get("preferredName"), "Legend Doe")
            self.assertEqual(
                data.get("address"),
                {"country": "US", "state": "US-CA", "street": "123 Main Street", "city": "Mill Valley", "zip": "94941"},
            )
            self.assertEqual(data.get("county_of_residence"), "Marin")
            self.assertEqual(data.get("username"), "John.Doe@calbright.org")
            self.assertEqual(data.get("accountDisabled"), False)
            self.assertEqual(data.get("accountBlocked"), "0")
            self.assertEqual(data.get("applicantType"), ["1"] if ccc_id == "CURRENT_STUDENT" else ["2"])
            self.assertEqual(data.get("enrollment_status"), "14" if ccc_id == "CURRENT_STUDENT" else "13")

            if ccc_id == "CURRENT_STUDENT":
                continue
            self.assertEqual(data.get("most_recent_certificate_comple"), "2023-08-17")
            for i in ["0060", "0200"]:
                self.assertIn(i, data.get("calbright_programs_completed"))

    def bulk_custom_query_operation(self, query, max_tries, dict_format):
        self.assertEqual(max_tries, 10)
        self.assertTrue(dict_format)
        if self.sf_query_count == 0:
            self.assertEqual(
                query,
                "SELECT cfg_CCC_ID__c, cfg_Calbright_Email__c, FirstName, LastName, cfg_Full_Name__c, "
                "Chosen_First_Name__c, Chosen_Last_Name__c, Email, cfg_Intended_Program__c, cfg_Learner_Status__c, "
                "Date_of_Enrollment__c, Current_Term_End_Date_c__c, MailingStreet, MailingCity, MailingPostalCode, "
                "Phone, MobilePhone, Leave_Start_Date__c, Leave_End_Date__c, HasOptedOutOfEmail, SMS_Opt_Out__c, "
                "DoNotCall, Assigned_Academic_Counselor_Email__c, Legal_First_Name__c FROM Contact WHERE Test_Demo__c "
                "= false and cfg_Learner_Status__c  in ('Completed Program Pathway', 'Started Program Pathway') and "
                "RecordTypeId = '0123k000001MQDqAAO'",
            )
            self.sf_query_count += 1
            return [self.current_student]
        self.assertEqual(
            query,
            "SELECT Contact__r.cfg_CCC_ID__c, Contact__r.cfg_Calbright_Email__c, Contact__r.FirstName, "
            "Contact__r.LastName, Contact__r.cfg_Full_Name__c, Contact__r.Chosen_First_Name__c, "
            "Contact__r.Chosen_Last_Name__c, Contact__r.Email, Contact__r.cfg_Intended_Program__c, "
            "Contact__r.cfg_Learner_Status__c, Contact__r.Date_of_Enrollment__c, "
            "Contact__r.Current_Term_End_Date_c__c, Contact__r.MailingStreet, Contact__r.MailingCity, "
            "Contact__r.MailingPostalCode, Contact__r.Phone, Contact__r.MobilePhone, Contact__r.Leave_Start_Date__c, "
            "Contact__r.Leave_End_Date__c, Contact__r.HasOptedOutOfEmail, Contact__r.SMS_Opt_Out__c, "
            "Contact__r.DoNotCall, Contact__r.Assigned_Academic_Counselor_Email__c, Contact__r.Legal_First_Name__c, "
            "Enrollment_Status_Date__c, Program_Name__c FROM Program_Enrollments__c WHERE "
            "Contact__r.Test_Demo__c = false and Enrollment_Status__c ='Complete'",
        )
        return self.alumni_students


if __name__ == "__main__":
    unittest.main()
