from datetime import datetime
from dateutil.parser import parse

from propus.aws.ssm import AWS_SSM
from propus.gsuite.user_directory import UserDirectory
from propus.salesforce import Salesforce
from propus import Logging


class MissingAnthologyTerm(Exception):
    pass


class VerifyStudents:
    def __init__(self, gsuite, sforce):
        self.gsuite = gsuite
        self.sforce = sforce

        self.logger = Logging.get_logger("verify_students.py")
        self.pre_enrolled_ou_statuses = [
            "App Submitted",
            "Ready for Onboarding",
            "Started Orientation",
            "Completed Orientation",
            "Completed CSEP",
        ]
        self.enrolled_ou_statuses = [
            "Enrolled in Program Pathway",
            "Started Program Pathway",
            "Completed Program Pathway",
        ]

        self.should_suspend_statuses = ["Dropped", "Suspended by IT (pre-enrollment)"]
        self.staff_ous = ["/Staff", "/Staff/Staff (with calbright-students.slack.com access)"]

        self.crm_ou = "/Enrolled Students/CRM Platform Admin Program"
        self.non_crm_ou = "/Enrolled Students"

    @staticmethod
    def build():
        ssm = AWS_SSM.build()
        return VerifyStudents(
            gsuite=UserDirectory.build(
                ssm.get_param("gsuite.calbright-student.users", param_type="json"), readonly=False
            ),
            sforce=Salesforce.build_v2("prod", ssm),
        )

    def run(self):
        all_users = self.gsuite.fetch_all_users(active=True, suspended=True)
        all_user_map = {user.get("primaryEmail"): user for user in all_users}

        salesforce_students = self.sforce.bulk_custom_query_operation(
            "SELECT cfg_Calbright_Email__c, cfg_Learner_Status__c, LastModifiedDate, cfg_Intended_Program__c, "
            "cfg_Learner_Status_Timestamp__c FROM Contact WHERE cfg_Calbright_Email__c != null AND Test_Demo__c = "
            "false ORDER BY cfg_Learner_Status__c",
            max_tries=4,
            dict_format=True,
        )

        sf_map = {student.get("cfg_Calbright_Email__c"): student for student in salesforce_students}
        self.logger.info(f"Retrieved {len(all_user_map.keys())} emails from gsuite")
        self.logger.info(f"Retrieved {len(sf_map.keys())} emails from salesforce")

        completed_student_resp = self.sforce.bulk_custom_query_operation(
            "SELECT Contact__r.cfg_Calbright_Email__c FROM Program_Enrollments__c WHERE "
            "Enrollment_Status__c = 'Complete'",
            max_tries=4,
            dict_format=True,
        )
        completed_student_emails = [cs.get("Contact__r.cfg_Calbright_Email__c") for cs in completed_student_resp]

        exist_only_in_sf = set(sf_map.keys()) - set(all_user_map.keys())
        self.logger.info(f"{len(exist_only_in_sf)} emails exist only in salesforce")

        exist_only_in_gsuite = set(all_user_map.keys()) - set(sf_map.keys())
        self.logger.info(f"{len(exist_only_in_gsuite)} emails exist only in gsuite")

        alumni_accounts_updated = 0
        pre_enrolled_accounts_updated = 0
        enrolled_accounts_updated = 0
        accounts_suspended = 0
        last_logins_by_year = {}

        for email, student in sf_map.items():
            gsuite_account = all_user_map.get(email)
            if not gsuite_account:
                if student.get("cfg_Learner_Status_Timestamp__c"):
                    learner_status_delta = datetime.now() - parse(
                        student.get("cfg_Learner_Status_Timestamp__c")
                    ).replace(tzinfo=None)
                    if learner_status_delta.days <= 60:
                        self.logger.info(f"   - ERROR: {email} does not exist in gsuite")
                continue
            student_ou = gsuite_account.get("orgUnitPath")
            if student_ou in self.staff_ous:
                continue

            if email in completed_student_emails:
                if gsuite_account.get("suspended") or student_ou not in [self.crm_ou, self.non_crm_ou]:
                    ou = self.crm_ou if student.get("cfg_Intended_Program__c") == "T2T CRM Admin" else self.non_crm_ou
                    self.gsuite.update_user_org_unit(email, ou, suspended=False)
                    alumni_accounts_updated += 1
            elif student.get("cfg_Learner_Status__c") in self.pre_enrolled_ou_statuses:
                if gsuite_account.get("suspended") or student_ou != "/Pre-enrolled Students":
                    self.gsuite.update_user_org_unit(email, "/Pre-enrolled Students", suspended=False)
                    pre_enrolled_accounts_updated += 1
            elif student.get("cfg_Learner_Status__c") in self.enrolled_ou_statuses:
                if (
                    gsuite_account.get("suspended")
                    or (student.get("cfg_Intended_Program__c") == "T2T CRM Admin" and student_ou != self.crm_ou)
                    or (student.get("cfg_Intended_Program__c") != "T2T CRM Admin" and student_ou != self.non_crm_ou)
                ):
                    ou = self.crm_ou if student.get("cfg_Intended_Program__c") == "T2T CRM Admin" else self.non_crm_ou
                    self.gsuite.update_user_org_unit(email, ou, suspended=False)
                    enrolled_accounts_updated += 1
            elif (
                not gsuite_account.get("suspended")
                and student.get("cfg_Learner_Status__c") in self.should_suspend_statuses
            ):
                self.gsuite.update_user_org_unit(email, "/Suspended", suspended=False)
                accounts_suspended += 1

            if not gsuite_account.get("suspended"):
                last_login_year = parse(gsuite_account.get("lastLoginTime")).year
                last_logins_by_year[last_login_year] = last_logins_by_year.get(last_login_year, 0) + 1

        self.logger.info(f"There are {alumni_accounts_updated} alumni accounts that were re-activated")
        self.logger.info(f"There are {accounts_suspended} accounts that should be suspended but are not")
        self.logger.info(f"There are {pre_enrolled_accounts_updated} PE accounts that should be activated/adjusted")
        self.logger.info(f"There are {enrolled_accounts_updated} E accounts that should be activated/adjusted")
