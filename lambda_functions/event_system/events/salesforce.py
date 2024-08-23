import threading
from datetime import datetime
from zoneinfo import ZoneInfo

from propus.calbright_sql.learner_status import LearnerStatus
from propus.calbright_sql.user import User
from propus.logging_utility import Logging
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from constants.hubspot_template_ids import (
    AUTOMATIC_DROP_DEVICE,
    AUTOMATIC_DROP_STAFF,
    AUTOMATIC_DROP_STUDENT,
)
from events.base import BaseEventSystem, is_feature_enabled


class SalesforceEvent(BaseEventSystem):
    __event_type__ = "salesforce_event"
    _required_fields = ["Student__r"]

    def __init__(self, configs, calbright, gsuite_licensing, gsuite_users, hubspot, salesforce, strut):
        super().__init__(configs)
        self.logger = Logging.get_logger("castor/lambda_functions/event_system/event/salesforce_event")
        self.calbright = calbright
        self.gsuite_licensing = gsuite_licensing
        self.gsuite_users = gsuite_users
        self.hubspot = hubspot
        self.salesforce = salesforce
        self.strut = strut
        self.processed_students = set()
        self.timestamp = datetime.now(tz=ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%S.000+0000")

        emails = self.constants.get("email", {})
        self.email_admissions = emails.get("admissions", "admissions@calbright.org")
        self.email_dev = emails.get("dev", "dev@calbright.org")
        self.email_enrollment_services = emails.get("enrollment_services", "kadisha.zohara@calbright.org")
        self.email_initiatives = emails.get("initiatives", "tamika@calbright.org")
        self.email_learning = emails.get("learning", "learning@calbright.org")
        self.email_registrar = emails.get(
            "registrar",
            "registrar@calbright.org",
        )
        self.email_security = emails.get(
            "security",
            "security@calbright.org",
        )
        self.email_success = emails.get("success", "success@calbright.org")
        self.email_veterans = emails.get("veterans", "veteranservices@calbright.org")

        self.link_catalog = self.constants.get("link", {}).get("catalog", "https://www.calbright.org/catalog")

        drop_reason = "Student Dropped"
        email_prefix = "Per your request, we have withdrawn you from your course of study."
        email_suffix = ""
        self.email_fields = dict(
            drop_reason=drop_reason,
            email_prefix=email_prefix,
            email_suffix=email_suffix,
        )

        drop_reason_automatic = "No participation within 30 days of enrollment"
        email_prefix_automatic = (
            """Our records indicate that you haven’t completed coursework within the first 30 days of your new class enrollment – therefore, our policies require that we drop you from your course of study.*"""  # noqa: E501
            + """
            Therefore, after multiple attempts to contact you, this is a notification that you’ve been withdrawn from Calbright College due to a lack of participation in your program pathway."""  # noqa: E501
        )
        email_suffix_automatic = f"""* Per our Academic Catalog (<a href="{self.link_catalog}" target="_blank">{self.link_catalog}</a>), students will have to establish participation in the online course content by submitting at least one assignment within the first 30 days of their enrollment. If a student does not submit at least one assignment within the first 30 days, they will be administratively dropped for non-participation."""  # noqa: E501
        self.email_fields_automatic = dict(
            drop_reason=drop_reason_automatic,
            email_prefix=email_prefix_automatic,
            email_suffix=email_suffix_automatic,
        )

        drop_reason_saa = "No substantive academic activity within the last 60 days"
        email_prefix_saa = "Our records indicate that you have not completed any coursework for 60 days or more.*  Therefore, after multiple attempts to contact you, this is a notification that you have been withdrawn from Calbright College due to a lack of participation in your program pathway."  # noqa: E501
        email_suffix_saa = """* Per course policy, students may be dropped for lack of academic engagement after 61 consecutive days of inactivity."""  # noqa: E501
        self.email_fields_saa = dict(
            drop_reason=drop_reason_saa,
            email_prefix=email_prefix_saa,
            email_suffix=email_suffix_saa,
        )

        drop_reason_registrar = "Registrar Initiated"
        email_prefix_registrar = f"""You have been withdrawn from your course of study. If you feel this was done in error please email Admissions and Records at <a href="mailto:{self.email_admissions}>{self.email_admissions}</a>"""  # noqa: E501
        self.email_fields_registrar = dict(
            drop_reason=drop_reason_registrar,
            email_prefix=email_prefix_registrar,
            email_suffix=email_suffix,
        )

    @staticmethod
    def build(configs, ssm):
        from services.calbright_client import CalbrightClient
        from services.gsuite_licensing_client import GoogleSuiteLicensingService
        from services.gsuite_user_directory_client import GoogleSuiteUserDirectoryService
        from services.hubspot_client import HubspotClient
        from services.salesforce_client import SalesforceService
        from services.strut_client import StrutService

        return SalesforceEvent(
            configs=configs,
            calbright=CalbrightClient(configs.get("calbright_write_ssm"), ssm),
            gsuite_licensing=GoogleSuiteLicensingService(configs.get("gsuite_svc_ssm"), ssm),
            gsuite_users=GoogleSuiteUserDirectoryService(configs.get("gsheets_ssm"), ssm, readonly=False),
            hubspot=HubspotClient(configs.get("hubspot_ssm"), ssm),
            salesforce=SalesforceService(configs.get("salesforce_ssm"), ssm),
            strut=StrutService(configs.get("strut_ssm"), ssm),
        )

    def run(self, event):
        threads = []
        for each_event in self.yield_bulk_data(self.__event_type__, event):
            thread_event = threading.local()
            payload = threading.local()
            thread_event = each_event | dict(learner_status="Dropped", timestamp=self.timestamp)
            self.check_required_fields(self.__event_type__, thread_event, self._required_fields)
            payload = self.create_payload(thread_event)
            threads.append(threading.Thread(target=self.update_learner_status_db, args=(payload,)))
            threads.append(threading.Thread(target=self.update_learner_status_salesforce, args=(payload,)))
            threads.append(threading.Thread(target=self.deprovision_gsuite, args=(payload,)))
            threads.append(threading.Thread(target=self.deprovision_strut, args=(payload,)))
            threads.append(threading.Thread(target=self.send_drop_emails, args=(payload,)))

        for t in threads:
            t.start()
            try:
                t.join()
            except RuntimeError as err:
                if 'cannot join current thread' in err:
                    continue
                else:
                    raise

    def create_payload(self, event_data):
        try:
            event_trigger = event_data.get("event", "").lower()
            if event_trigger == "automatic_drop":
                email_fields = self.email_fields_automatic
            elif event_trigger == "registrar_drop":
                email_fields = self.email_fields_registrar
            elif event_trigger == "saa_drop":
                email_fields = self.email_fields_saa
            else:
                email_fields = self.email_fields

        except Exception:
            email_fields = self.email_fields

        try:
            student = event_data.get("Student__r", {})

            return {
                "calbright_email": student.get("cfg_Calbright_Email__c", ""),
                "ccc_id": student.get("cfg_CCC_ID__c", ""),
                "counselor_email": student.get("cfg_Assigned_Learner_Advocate__r", {}).get(
                    "Email", self.constants.get("email", {}).get("counselor", "asc@calbright.org")
                ),
                "email": student.get("Email", ""),
                "drop_program": student.get("cfg_Intended_Program__c", ""),
                "learner_status": event_data.get("learner_status", ""),
                "name": student.get("Name", ""),
                "requested_chromebook": student.get("cfg_Chromebook_Requested__c", False),
                "requested_hotspot": student.get("cfg_Hotspot_Requested__c", False),
                "sf_id": student.get("Id", ""),
                "strut_id": student.get("cfg_Strut_User_ID__c", ""),
                "timestamp": event_data.get("timestamp"),
            } | email_fields
        except Exception as err:
            self.logger.error(f"Error creating payload with {event_data}: {err}")

    @is_feature_enabled
    def deprovision_gsuite(self, payload):
        try:
            calbright_email = payload.get("calbright_email")
            if not calbright_email:
                self.logger.warning(
                    f"No GSuite email to deprovision for ccc_id {payload.get('ccc_id')} / Salesforce Id {payload.get('sf_id')}"  # noqa: E501
                )
                return

            try:
                self.gsuite_users.suspend_student(calbright_email)
                self.logger.info(f"Suspended student from GSuite {calbright_email}")
            except Exception as err:
                self.logger.error(f"Error suspending student from GSuite {calbright_email}: {err}")

            try:
                self.gsuite_licensing.delete_license(calbright_email)
                self.logger.info(f"Deleted student license if existed from GSuite {calbright_email}")
            except Exception as err:
                self.logger.error(f"Error deleting student license from GSuite {calbright_email}: {err}")

        except Exception as err:
            self.logger.error(f"Error deprovisioning student from GSuite with {payload}: {err}")

    @is_feature_enabled
    def deprovision_strut(self, payload):
        try:
            strut_id = payload.get("strut_id")
            if not strut_id:
                self.logger.info("Skipping deprovision_strut... no strut_id provided")
                return

            try:
                self.strut.lock_student_enrollments(strut_id)
                self.logger.info(f"Strut enrollments locked for strut_id {strut_id}")
            except Exception as err:
                self.logger.error(f"Error locking enrollments for strut_id {strut_id}: {err}")

            try:
                self.strut.withdraw_student(strut_id)
                self.logger.info(f"Strut withdrawn for strut_id {strut_id}")
            except Exception as err:
                self.logger.error(f"Error withdrawing for strut_id {strut_id}: {err}")

        except Exception as err:
            self.logger.error(f"Error deprovisioning student from Strut with {payload}: {err}")

    @is_feature_enabled
    def send_drop_emails(self, payload):
        try:
            calbright_email = payload.get("calbright_email")
            ccc_id = payload.get("ccc_id")
            counselor_email = payload.get("counselor_email")
            email = payload.get("email")
            name = payload.get("name")
            requested_chromebook = payload.get("requested_chromebook")
            requested_hotspot = payload.get("requested_hotspot")

            calbright_address = f"{name} <{calbright_email}>"
            personal_address = f"{name} <{email}>"

            try:
                if requested_chromebook or requested_hotspot:
                    if requested_chromebook and requested_hotspot:
                        payload["device"] = "Chromebook and T-Mobile hotspot"
                    elif requested_chromebook:
                        payload["device"] = "Chromebook"
                    elif requested_hotspot:
                        payload["device"] = "T-Mobile hotspot"
                    else:
                        payload["device"] = "Chromebook and/or T-Mobile hotspot"
                    # Email the Student to ask them to return their device
                    self.hubspot.send_transactional_email(
                        email_id=AUTOMATIC_DROP_DEVICE,
                        to_email=personal_address,
                        cc=[calbright_address],
                        bcc=[self.email_security],
                        custom_properties=payload,
                    )
                    self.logger.info(f"Device email sent to student ccc_id {ccc_id}")

            except Exception as err:
                self.logger.error(f"Error sending device email to student ccc_id {ccc_id}: {err}")

            try:
                # Email the Student notifying them that they have been dropped
                self.hubspot.send_transactional_email(
                    email_id=AUTOMATIC_DROP_STUDENT,
                    to_email=personal_address,
                    cc=[
                        self.email_registrar,
                        self.email_learning,
                        counselor_email,
                    ],
                    bcc=[self.email_enrollment_services, self.email_initiatives],
                    custom_properties=payload,
                )
                self.logger.info(f"Student drop email sent to student ccc_id {ccc_id}")
            except Exception as err:
                self.logger.error(f"Error sending student drop email to student ccc_id {ccc_id}: {err}")

            try:
                # Email Calbright staff notifying them of the Student dropped
                self.hubspot.send_transactional_email(
                    email_id=AUTOMATIC_DROP_STAFF,
                    to_email=self.email_registrar,
                    cc=[self.email_initiatives],
                    bcc=[self.email_dev],
                    custom_properties=payload,
                )
                self.logger.info(f"Staff drop email sent for student ccc_id {ccc_id}")
            except Exception as err:
                self.logger.error(f"Error sending staff drop email for student ccc_id {ccc_id}: {err}")

        except Exception as err:
            self.logger.error(f"Error sending emails with {payload}: {err}")

    @is_feature_enabled
    def update_learner_status_db(self, payload):
        try:
            ccc_id = payload.get("ccc_id")
            learner_status = payload.get("learner_status")
            user = self.calbright.session.execute(select(User).filter_by(ccc_id=ccc_id)).scalar_one()
        except NoResultFound:
            self.logger.error(f"User not found for ccc_id {ccc_id}")
            return
        except Exception as err:
            self.logger.error(f"Error getting User: {err}")
            return

        try:
            user.learner_status = self.calbright.session.execute(
                select(LearnerStatus).filter_by(status=learner_status)
            ).scalar_one()
            self.calbright.session.commit()
            self.logger.info(f"Updated {ccc_id} to learner status {learner_status}")
        except NoResultFound:
            self.logger.error(f"Learner status not found {learner_status}")
        except Exception as err:
            self.logger.error(f"Error getting LearnerStatus: {err}")

    @is_feature_enabled
    def update_learner_status_salesforce(self, payload):
        try:
            sf_id = payload.get("sf_id")
            data = {
                "cfg_Learner_Status__c": payload.get("learner_status"),
                "cfg_Learner_Status_Timestamp__c": payload.get("timestamp"),
                "Pilot_PostEnrollmentEmailSent__c": False,
            }
            self.salesforce.client.update_contact_record(sf_id, **data)
            self.logger.info(f"Update Salesforce for contact {sf_id}")
        except Exception as err:
            self.logger.error(f"Error updating Salesforce: {err}")
