from propus.helpers.sql_alchemy import build_query
from propus.helpers.etl import fetch_county
from propus import Logging


def fetch_csm_picklist_data(csm):
    picklist_types = {
        "applicantType": "current_status",
        "enrollment_status": "learner_status",
        "majors": "intended_program",
        "calbright_programs_completed": "programs_complete",
    }
    intended_program = {
        "Transition to Technology: CRM Platform Administration": "T2T CRM Admin",
        "Upskilling to Equitable Health Impact: Diversity, Equity, and Inclusion": "HC DEI",
        "Transition To Technology: Introduction to Networks": "T2T Intro to Networks",
    }
    program_enrollment_names = {
        "Transition to Technology: CRM Platform Administration": "Customer Relationship Management",
        "Upskilling to Equitable Health Impact: Diversity, Equity, and Inclusion": "HC DEI",
        "Transition To Technology: Introduction to Networks": "T2T Intro to Networks",
    }
    picklist_dict = {}
    for csm_name, calbright_name in picklist_types.items():
        sf_names = intended_program if calbright_name == "intended_program" else program_enrollment_names
        response = csm.fetch_form_picklist(csm_name)
        picklist_dict[calbright_name] = {
            sf_names.get(r.get("value")) if sf_names.get(r.get("value")) else r.get("value"): r.get("id")
            for r in response
        }
    return picklist_dict


class SalesforceService:
    def __init__(self, sforce, csm_keys):
        self.sforce = sforce

        self.csm_keys = csm_keys
        self.logger = Logging.get_logger("salesforce_service.py")

    @staticmethod
    def build(sforce, csm):
        csm_keys = fetch_csm_picklist_data(csm) | {
            "counselors": {r.get("email"): r.get("id") for r in csm.list_staff().get("models")}
        }
        return SalesforceService(sforce, csm_keys)

    def lookup_value(self, key: str, value: str):
        """Lookup value from mapping keys

        This function looks up a value given a key and value, and returns a
        normalized key and value. It checks the provided 'key' against a set of known
        keys and returns the corresponding normalized key and mapped value.

        Args:
            key (str): The key to lookup
            value (str): The value associated with the key

        Returns:
            tuple: A 2-item tuple containing the normalized key and mapped value
        """
        if key == "cfg_Learner_Status__c":
            return "enrollment_status", self.csm_keys.get("learner_status").get(value)
        if key == "cfg_Intended_Program__c":
            return "majors", [self.csm_keys.get("intended_program").get(value)]
        if key == "Assigned_Academic_Counselor_Email__c":
            return "counselors", (
                [self.csm_keys.get("counselors").get(value)] if self.csm_keys.get("counselors").get(value) else []
            )
        if key == "Program_Name__c":
            return "calbright_programs_completed", [self.csm_keys.get("programs_complete").get(value)]

    @staticmethod
    def format_date(key: str, value: str):
        """Format date value

        This function formats a date value based on the provided key and value.
        It checks the provided 'key' against a set of known keys and returns the
        corresponding formatted date value.

        Args:
            key (str): The key to format
            value (str): The value associated with the key

        Returns:
            tuple: A 2-item tuple containing the formatted key and date value
        """
        dict_map = {
            "Date_of_Enrollment__c": "date_of_enrollment",
            "Current_Term_End_Date_c__c": "current_end_term_date",
            "Leave_Start_Date__c": "leave_start_date",
            "Leave_End_Date__c": "leave_end_date",
            "Enrollment_Status_Date__c": "most_recent_certificate_comple",
        }
        return dict_map.get(key), value.split("T")[0] if value else None

    @staticmethod
    def format_boolean(key: str, value: str):
        """Format boolean value

        This function formats a boolean value based on the provided key and value.
        It checks the provided 'key' against a set of known keys and returns the
        corresponding formatted boolean value.

        Args:
            key (str): The key to format
            value (str): The value associated with the key

        Returns:
            tuple: A 2-item tuple containing the formatted key and boolean value
        """
        key_dict = {"HasOptedOutOfEmail": "email_opt_out", "SMS_Opt_Out__c": "sms_opt_out", "DoNotCall": "do_not_call"}
        return key_dict.get(key), True if value == "true" else False

    def fetch_csm_eligible_students(self, ccc_ids=None, disabled=False):
        """Fetch eligible students from Salesforce.

        This function queries Salesforce to retrieve student records that are
        eligible for CSM (SSP status or Completed at least 1 program). It maps
        the Salesforce fields to normalized  field names and formats dates/booleans.
        Records are aggregated and deduplicated based on the schoolStudentId (CCC ID).

        The results are returned as a dictionary with the student ID as the key
        and student data as the value.

        Returns:
            dict: A dictionary of eligible student records with student CCC ID as key
        """
        data_fields_mapping = {
            "cfg_CCC_ID__c": "schoolStudentId",
            "cfg_Calbright_Email__c": "email",
            "FirstName": "firstName",
            "LastName": "lastName",
            "cfg_Full_Name__c": "fullName",
            "Chosen_First_Name__c": None,
            "Chosen_Last_Name__c": None,
            "Email": "permanentEmail",
            "cfg_Intended_Program__c": self.lookup_value,
            "cfg_Learner_Status__c": self.lookup_value,
            "Date_of_Enrollment__c": self.format_date,
            "Current_Term_End_Date_c__c": self.format_date,
            "MailingStreet": "street",
            "MailingCity": "city",
            "MailingPostalCode": "zip",
            "Phone": "phone",
            "MobilePhone": "mobile_phone_number",
            "Leave_Start_Date__c": self.format_date,
            "Leave_End_Date__c": self.format_date,
            "HasOptedOutOfEmail": self.format_boolean,
            "SMS_Opt_Out__c": self.format_boolean,
            "DoNotCall": self.format_boolean,
            "Assigned_Academic_Counselor_Email__c": self.lookup_value,
            "Legal_First_Name__c": "legal_first_name",
        }
        results = None
        if not ccc_ids:
            qry = build_query(
                table="Contact",
                fields=list(data_fields_mapping.keys()),
                filters=[
                    "Test_Demo__c = false",
                    "cfg_Learner_Status__c  in ('Completed Program Pathway', 'Started Program Pathway')",
                    "RecordTypeId = '0123k000001MQDqAAO'",
                ],
            )
            results = self.sforce.bulk_custom_query_operation(qry, max_tries=10, dict_format=True)
            qry = build_query(
                table="Program_Enrollments__c",
                fields=[f"Contact__r.{f}" for f in data_fields_mapping.keys()]
                + ["Enrollment_Status_Date__c", "Program_Name__c"],
                filters=[
                    "Contact__r.Test_Demo__c = false",
                    "Enrollment_Status__c ='Complete'",
                ],
            )

            results += self.sforce.bulk_custom_query_operation(qry, max_tries=10, dict_format=True)
        else:
            joined_cccids = "','".join(ccc_ids)
            qry = build_query(
                table="Contact",
                fields=list(data_fields_mapping.keys()),
                filters=[
                    f"cfg_CCC_ID__c IN ('{joined_cccids}')",
                    "RecordTypeId = '0123k000001MQDqAAO'",
                ],
            )
            results = self.sforce.bulk_custom_query_operation(qry, max_tries=10, dict_format=True)

        self.logger.info(f"Retrieved {len(results)} records from salesforce")
        data_fields_mapping["Enrollment_Status_Date__c"] = self.format_date
        data_fields_mapping["Program_Name__c"] = self.lookup_value
        salesforce_students = {}
        for result in results:
            data = {}
            address = {"country": "US", "state": "US-CA"}
            keys = list(result.keys())
            for key in keys:
                new_key = key.replace("Contact__r.", "")

                if data_fields_mapping.get(new_key):
                    if type(data_fields_mapping.get(new_key)) == str:
                        if "Mailing" in new_key:
                            if result.get(key):
                                address[data_fields_mapping.get(new_key)] = result.get(key)
                        else:
                            data[data_fields_mapping.get(new_key)] = result.get(key)
                    else:
                        if key == "Assigned_Academic_Counselor_Email__c" and result.get(key).endswith(".invalid"):
                            result[key] = result.get(key)[:-8]
                        k, v = data_fields_mapping.get(new_key)(new_key, result.get(key))
                        data[k] = v

            if result.get("Chosen_First_Name__c") and result.get("Chosen_Last_Name__c"):
                data["preferredName"] = f"{result.get('Chosen_First_Name__c')} {result.get('Chosen_Last_Name__c')}"
            if result.get("Contact__r.Chosen_First_Name__c") and result.get("Contact__r.Chosen_Last_Name__c"):
                data["preferredName"] = (
                    f"{result.get('Contact__r.Chosen_First_Name__c')} {result.get('Contact__r.Chosen_Last_Name__c')}"
                )

            data["address"] = address
            data["county_of_residence"] = fetch_county(address.get("city"), address.get("zip"))
            data["username"] = data.get("email")
            data["accountDisabled"] = False
            data["accountBlocked"] = "0"
            if disabled:
                data["accountDisabled"] = True
                data["accountBlocked"] = "1"

            for key in [
                "leave_start_date",
                "leave_end_date",
                "most_recent_certificate_comple",
                "current_end_term_date",
                "last_term_enrolled",
            ]:
                if key in data and not data.get(key):
                    del data[key]

            if data.get("legal_first_name") and data.get("firstName") != data.get("legal_first_name"):
                # Student has a preferred name and firstName should be reset to legal name
                data["firstName"] = data.get("legal_first_name")
            del data["legal_first_name"]

            data["applicantType"] = [
                (
                    self.csm_keys.get("current_status").get("Current Student")
                    if result.get("cfg_Learner_Status__c") == "Started Program Pathway"
                    else self.csm_keys.get("current_status").get("Alumni")
                )
            ]
            if salesforce_students.get(data.get("schoolStudentId")):
                salesforce_students.get(data.get("schoolStudentId"))["most_recent_certificate_comple"] = max(
                    [
                        data.get("most_recent_certificate_comple", ""),
                        salesforce_students.get(data.get("schoolStudentId")).get("most_recent_certificate_comple", ""),
                    ]
                )
                salesforce_students.get(data.get("schoolStudentId"))["calbright_programs_completed"] = sorted(
                    list(
                        set(
                            salesforce_students.get(data.get("schoolStudentId")).get("calbright_programs_completed", [])
                            + data.get("calbright_programs_completed", [])
                        )
                    )
                )
                continue
            salesforce_students[data.get("schoolStudentId")] = data
        self.logger.info(f"Retrieved {len(salesforce_students)} students from salesforce")
        return salesforce_students
