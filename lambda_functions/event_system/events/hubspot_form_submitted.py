import re
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from typing import AnyStr, Dict, List

from propus.calbright_sql.expressed_interest import ExpressInterest, BrowserType, LeadSource
from propus.calbright_sql.learner_status import LearnerStatus
from propus.calbright_sql.program import Program
from propus.calbright_sql.user import User
from propus.helpers.sql_alchemy import find_enum_value
from propus.helpers.calbright import PROGRAM_SHORT_NAME_TO_SF_API_NAME
from propus.logging_utility import Logging

from constants.hubspot_template_ids import STUDENT_INTENDED_PROGRAM_CHANGE
from events.base import BaseEventSystem
from exceptions import MissingRequiredField

FORM_ID_PROGRAM_NAME_MAP = {
    "f0842358-1fe4-45c0-a823-769157308c95": "Enroll",
    "c8ada9a4-28f7-4b5c-8e0a-22b0af60f75f": "Pre-Apply Networks",
    "15cc3bf4-431b-49d1-8137-8ecc0fc59d49": "Pre-Apply DA",
    "bda4c4fb-fe56-43ee-84b6-daa384a2f912": "Pre-Apply CRM",
    "a5dff3ad-b46c-4a80-ba01-a062c01f6e7e": "Pre-Apply Project Management",
    "3b4e6bcc-7450-40d5-bdd5-57eb9f4fb3f8": "Pre-Apply Cybersecurity",
    "6105d9a8-5ffe-4fee-8a0a-ebaed19623b9": "Pre-Apply IT Support",
    "e71bf9f3-f63f-4473-8cc1-adcbbfe2d327": "Step2 Networks",
    "83ea8b83-757c-4bf6-a1e5-14e07f199e4f": "Step2 DA",
    "6a7eac57-7e98-42d8-bfbe-a71cc0793c2c": "Step2 CRM",
    "aeaa5e2a-ea01-4913-b986-74fade33c451": "Step2 Project Management",
    "460b782b-23e2-4740-9745-ff454244dc99": "Step2 Cybersecurity",
    "6db42f6a-1591-4caf-87ca-a5ac08dc6c62": "Step2 IT Support",
}

LEARNER_STATUS_UPDATE_TABLE = {
    "App Started": "App Started",
    "Expressed Interest": "App Started",
    "Completed Program Pathway": "App Submitted",
}


class HubspotFormSubmitted(BaseEventSystem):
    __event_type__ = "hubspot_forms_submission"

    _required_fields = ["properties"]
    _required_properties = [
        "email",
        "program_of_interest",
        "phone",
        "firstname",
        "lastname",
        "hs_calculated_form_submissions",
    ]

    def __init__(self, configs, ssm, salesforce, hubspot, calbright):
        super().__init__(configs, ssm)
        self.logger = Logging.get_logger("castor/lambda_functions/event_system/event/hubspot_forms_submission")
        self.salesforce = salesforce
        self.hubspot = hubspot
        self.calbright = calbright

    def upsert_user(
        self,
        email: AnyStr,
        first_name: AnyStr,
        last_name: AnyStr,
        phone: AnyStr,
        properties: Dict,
        program_of_interest: AnyStr,
        learner_status="Expressed Interest",
        programs_of_interest: List = [],
        user=None,
        new_program=True,
    ):
        program_set = set(programs_of_interest)
        program_set.add(program_of_interest)

        l_status = self.calbright.session.execute(select(LearnerStatus).filter_by(status=learner_status)).scalar_one()
        properties["browser_type"] = self.get_browser_type(properties.get("user_agent", {}).get("value"))
        allow_sms = properties.get("I agree to receive text updates from Calbright College.", {}).get("value", False)
        salesforce_data = {
            "Email": email,
            "FirstName": first_name,
            "LastName": last_name,
            "cfg_Learner_Status__c": learner_status,
            "Phone": phone,
            "MobilePhone": phone,
            "HomePhone": phone,
            "OtherPhone": phone,
            "LeadSource": properties.get("hs_latest_source", {}).get("value"),
            "cfg_Landing_Page_URL__c": properties.get("handl_landing_page", {}).get("value"),
            "cfg_Referrer_URL__c": properties.get("handl_original_url", {}).get("value"),
            "cfg_UTM_Source__c": properties.get("utm_source", {}).get("value"),
            "cfg_UTM_Campaign__c": properties.get("utm_campaign", {}).get("value"),
            "cfg_UTM_Content__c": properties.get("utm_content", {}).get("value"),
            "cfg_UTM_Medium__c": properties.get("utm_medium", {}).get("value"),
            "cfg_UTM_Term__c": properties.get("utm_term", {}).get("value"),
            "cfg_Intended_Program__c": program_of_interest,
            "cfg_Programs_of_Interest__c": ";".join(list(program_set)),
            "cfg_Learner_Status_Timestamp__c": datetime.now(timezone.utc).isoformat(),
            "Pre_Application_Browser_Type__c": properties.get("browser_type"),
            "IP__c": properties.get("ip__c", {}).get("value"),
            "SMS_Opt_Out__c": not allow_sms or (user.sms_opt_out if user else False),
        }
        db_data = {
            "personal_email": email,
            "first_name": first_name,
            "last_name": last_name,
            "phone_number": phone,
            "learner_status_id": l_status.id,
            "sms_opt_out": not allow_sms,
        }
        if user:
            # Update
            self.salesforce.client.update_contact_record(user.salesforce_id, **salesforce_data)
            for key, value in db_data.items():
                setattr(user, key, value)
        else:
            # Create
            response = self.salesforce.client.create_contact_record("learner", **salesforce_data)
            db_data["salesforce_id"] = response.get("id")
            user = User(**db_data)
            self.calbright.session.add(user)
        self.calbright.session.flush()

        # Create Expressed Interest Record
        if new_program:
            self.create_expressed_interest_record(user_id=user.id, properties=properties)
        self.calbright.session.commit()

    def create_expressed_interest_record(self, user_id, properties):
        self.calbright.session.add(
            ExpressInterest(
                user_id=user_id,
                program_interest=self.calbright.session.execute(
                    select(Program).filter_by(short_name=properties.get("program_of_interest", {}).get("value"))
                ).scalar_one(),
                state_declared=properties.get("state_dropdown", {}).get("value"),
                browser_type=BrowserType(properties.get("browser_type")),
                landing_page=properties.get("handl_landing_page", {}).get("value"),
                lead_source=(
                    find_enum_value(LeadSource, properties.get("hs_latest_source", {}).get("value"))
                    if properties.get("hs_latest_source", {}).get("value")
                    else None
                ),
                utm_medium=properties.get("utm_medium", {}).get("value"),
                utm_term=properties.get("utm_term", {}).get("value"),
                utm_source=properties.get("utm_source", {}).get("value"),
                utm_content=properties.get("utm_content", {}).get("value"),
                utm_campaign=properties.get("utm_campaign", {}).get("value"),
                referrer_url=properties.get("handl_original_url", {}).get("value"),
                ip_address=properties.get("ip__c", {}).get("value"),
            )
        )

    @staticmethod
    def build(configs, ssm):
        from services.calbright_client import CalbrightClient
        from services.hubspot_client import HubspotClient
        from services.salesforce_client import SalesforceService

        return HubspotFormSubmitted(
            configs,
            ssm,
            salesforce=SalesforceService(configs.get("salesforce_ssm"), ssm),
            hubspot=HubspotClient(configs.get("hubspot_ssm"), ssm),
            calbright=CalbrightClient(configs.get("calbright_write_ssm"), ssm),
        )

    def run(self, event_data):
        self.check_required_fields(self.__event_type__, event_data, self._required_fields)
        properties = event_data.get("properties")
        self._check_required_properties(properties)
        form_id = properties.get("hs_calculated_form_submissions", {}).get("value").split(":")[0]
        if not FORM_ID_PROGRAM_NAME_MAP.get(form_id):
            self.logger.info(f"Received form id {form_id} not mapped for interest completion. Skipping.")
            return

        email = properties.get("email", {}).get("value")
        first_name = properties.get("firstname", {}).get("value").capitalize()
        last_name = properties.get("lastname", {}).get("value").capitalize()
        phone = properties.get("phone", {}).get("value")
        program_of_interest = properties.get("program_of_interest", {}).get("value")
        program_of_interest = (
            program_of_interest if program_of_interest != "Customer Relationship Management" else "T2T CRM Admin"
        )
        try:
            contact = self.calbright.session.execute(select(User).filter_by(personal_email=email)).scalar_one()
            programs_of_interest = [
                PROGRAM_SHORT_NAME_TO_SF_API_NAME.get(e.program_interest.short_name, e.program_interest.short_name)
                for e in contact.expressed_interest_user
            ]
        except NoResultFound:
            self.logger.info(
                f"New Expressed Interest by: {first_name} {last_name}. Registering new contact with email {email}."
            )
            self.upsert_user(email, first_name, last_name, phone, properties, program_of_interest)
            return

        current_program = programs_of_interest[0]
        learner_status = contact.learner_status.status
        if (
            learner_status in ["Ready for Onboarding", "Completed Orientation", "Completed CSEP"]
            or (learner_status == "Started Orientation" and current_program == "Customer Relationship Management")
        ) and current_program != program_of_interest:
            # If the student is Pre-Enrolled and they filled out a form with a different program of interest send
            # them an email:
            self.hubspot.send_transactional_email(
                email_id=STUDENT_INTENDED_PROGRAM_CHANGE,
                to_email=email,
                custom_properties={
                    "program_interested": program_of_interest,
                    "intended_program": current_program,
                    "first_name": first_name,
                },
            )
        elif learner_status in (
            "App Submitted",
            "Expressed Interest",
            "App Started",
            "Completed Program Pathway",
            "Dropped",
        ) or (learner_status == "Started Orientation" and current_program == "Customer Relationship Management"):

            if learner_status == "Completed Program Pathway" or learner_status == "Dropped":
                learner_status = "App Submitted"
            elif "Step2" in FORM_ID_PROGRAM_NAME_MAP.get(form_id) and learner_status in ["Expressed Interest"]:
                # If the student has filled out the intersticial form
                learner_status = "App Started"

            self.upsert_user(
                email,
                first_name,
                last_name,
                phone,
                properties,
                program_of_interest,
                learner_status,
                programs_of_interest=programs_of_interest,
                user=contact,
                new_program=current_program == program_of_interest,
            )

    def get_browser_type(self, user_agent):
        mobile_pattern = re.compile(
            r"/Mobile|iP(hone|od|ad)|Android|BlackBerry|IEMobile|Kindle|NetFront|Silk-Accelerated|"
            r"(hpw|web)OS|Fennec|Minimo|Opera M(obi|ini)|Blazer|Dolfin|Dolphin|Skyfire|Zune/",
            re.IGNORECASE,
        )
        return "Mobile" if bool(mobile_pattern.search(user_agent)) else "Desktop"

    def _check_required_properties(self, properties):
        for req_prop in self._required_properties:
            if req_prop not in properties or not properties.get(req_prop).get("value"):
                raise MissingRequiredField(event_type=self.__event_type__, field=req_prop)
