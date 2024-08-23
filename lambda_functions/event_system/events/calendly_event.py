from datetime import datetime, timezone
from enum import Enum
import re
from typing import AnyStr
from zoneinfo import ZoneInfo
from sqlalchemy import select

from propus.calbright_sql.learner_status import LearnerStatus
from propus.calbright_sql.user import User
from propus.logging_utility import Logging

from events.base import BaseEventSystem
from exceptions import UnknownCalendlyEventType, CalbrightEmailNotInDatabase


def convert_date_to_pst(date_string):
    if not date_string:
        return ""
    utc_date = datetime.now().strptime(date_string.split(".")[0], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    return utc_date.astimezone(tz=ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%dT%H:%M:%S.000000Z")


class EventTypeUUID(str, Enum):
    IT_SUPPORT = "6b973ef7-7921-48bc-b556-c14f285f84a1"
    CYBERSECURITY = "2a9f6c29-6e8f-480e-8c24-319776b79b28"
    MEDICAL_CODING = "1af36ba5-3e8e-416a-9776-85a980727e09"
    DATA_ANALYSIS = "f62a740b-153f-488b-85d0-806af299bfa7"
    DEI = "58a10b24-a6b9-4b60-8624-45a9239c40f1"
    CAREER_READINESS = "c1f7050e-4a08-4aa1-a665-ee69aef8415d"
    CRM = "GFH3KADHMS65FY6I"
    ONE_ON_ONE = "GAHKWQJBX5C3PCI4"
    T2T_INTRO_TO_NETWORKS = "cdb84f90-de44-4e82-b6ac-1134c314b356"
    PROJECT_MANAGEMENT = "4b634c8d-54ec-43da-bc10-a37959bf5519"


class CalendlyEvent(BaseEventSystem):
    __event_type__ = "calendly_event"

    _invitee_created_required_fields = ["email", "scheduled_event"]
    _scheduled_event_required_fields = ["event_type", "start_time", "location"]
    _invitee_canceled_required_fields = []

    def __init__(self, configs, salesforce, calendly, calbright):
        super().__init__(configs)

        self.logger = Logging.get_logger("castor/lambda_functions/event_system/event/calendly_event")
        self.salesforce = salesforce
        self.calendly = calendly
        self.calbright = calbright

        self.event_metadata = None

        self.event_map = {
            "invitee.canceled": self.process_canceled_event,
            "invitee.created": self.process_created_event,
        }
        self.check_fn = {"invitee.canceled": self.check_canceled_payload, "invitee.created": self.check_created_payload}
        self.calendly_event_name = None

    def check_created_payload(self, event_data):
        self.check_required_fields(self.__event_type__, event_data, self._invitee_created_required_fields)
        self.check_required_fields(
            self.__event_type__, event_data.get("scheduled_event"), self._scheduled_event_required_fields
        )

    def check_canceled_payload(self, event_data):
        self.check_required_fields(self.__event_type__, event_data, self._invitee_canceled_required_fields)

    @staticmethod
    def build(configs, ssm):
        from services.calendly_client import CalendlyClient
        from services.salesforce_client import SalesforceService
        from services.calbright_client import CalbrightClient

        return CalendlyEvent(
            configs=configs,
            calbright=CalbrightClient(configs.get("calbright_write_ssm"), ssm),
            calendly=CalendlyClient(configs.get("calendly_ssm"), ssm),
            salesforce=SalesforceService(configs.get("salesforce_ssm"), ssm),
        )

    def init_data(self, event_data):
        event_memberships = event_data.get("scheduled_event").get("event_memberships")
        event_type_uuid = event_data.get("scheduled_event", {}).get("event_type", "").split("/")[-1]
        host_user = event_memberships[0] if event_memberships else {}
        event_type = self.calendly.fetch_event_type(event_type_uuid).get("resource", {})

        self.event_metadata = {
            "event_type_uuid": event_type_uuid,
            "location": event_data.get("scheduled_event", {}).get("location", {}).get("join_url")
            or event_data.get("scheduled_event", {}).get("location", {}).get("location"),
            "event_kind": (
                event_type.get("pooling_type") if event_type.get("pooling_type") else event_type.get("kind")
            ).capitalize(),
            "event_type_name": event_type.get("name"),
            "event_type_slug": event_type.get("slug"),
            "event_duration": event_type.get("duration"),
            "start_time": event_data.get("scheduled_event").get("start_time"),
            "q_and_a": event_data.get("questions_and_answers", []),
            "created_at": event_data.get("created_at"),
            "text_reminder_number": event_data.get("text_reminder_number"),
            "cancelled_at": event_data.get("cancellation", {}).get("created_at"),
            "cancel_reason": event_data.get("cancellation", {}).get("reason"),
        }

        self.invitee_email = event_data.get("email")
        user_db_lookup = (
            self.calbright.session.execute(
                select(User).where(User.calbright_email.in_([self.invitee_email, host_user.get("user_email")]))
            )
            .scalars()
            .all()
        )

        user_map = {u.calbright_email: u for u in user_db_lookup}
        self.student_record = user_map.get(self.invitee_email)

        host = user_map.get(host_user.get("user_email"))
        self.calbright_user_id = (
            host.salesforce_id
            if host and host.salesforce_id
            else self.salesforce.get_calbright_user_by_email(host_user.get("user_email"))
        )

        # User Data
        self.user_data = (
            self.calendly.fetch_user(host_user.get("user", "").split("/")[-1]) if self.calbright_user_id else None
        )

    def run(self, event_data):
        event = event_data.get("event")
        if event in ["routing_form_submission.created"]:
            # We are not tracking these event types
            return
        elif event not in self.event_map:
            raise UnknownCalendlyEventType(event)
        self.calendly_event_name = event
        self.check_fn.get(event)(event_data.get("payload"))
        self.event_map.get(event)(event_data.get("payload"))

    def update_learner_status(self, status):
        self.salesforce.client.update_contact_record(self.student_record.salesforce_id, Cfg_Learner_Status__c=status)
        self.student_record.learner_status = self.calbright.session.execute(
            select(LearnerStatus).filter_by(status=status)
        ).scalar_one()

    def process_created_event(self, event_data):
        event_type = event_data.get("scheduled_event", {}).get("event_type", "")
        if event_type.split("/")[-1] not in iter(EventTypeUUID):
            self.logger.warning(f"calandly/invitee_created {event_type} not recognized")
            # TODO: Insert this into the database later...
            return

        self.init_data(event_data)
        if not self.student_record:
            if re.search(r"[a-z.0-9]+@calbrightcollege.(org|edu)", self.invitee_email):
                raise CalbrightEmailNotInDatabase(self.invitee_email)
        else:
            self.process_onboarding_session()
            self.store_event_in_salesforce()
            # TODO: Lookup the event in the database and mark it as scheduled for this user

    def process_canceled_event(self, event_data):
        self.init_data(event_data)
        if not self.student_record:
            if re.search(r"[a-z.0-9]+@calbrightcollege.(org|edu)", self.invitee_email):
                self.logger.error(f"calandly/invitee_canceled no student record found with email {self.invitee_email}")
        else:
            self.store_event_in_salesforce()
            # TODO: Lookup the event in the database and mark it as canceled

    def store_event_in_salesforce(self):
        event_payload = self.build_salesforce_payload()
        # Make create event call to salesforce
        response = self.salesforce.client.create_event(**event_payload)
        self.logger.info(f"successfully created event id {response.get('id')}")

    def create_description(self) -> AnyStr:
        """
        Function used to simply format the event description that is created in Salesforce

            Returns:
                description (str): formatted event description
        """
        description = f"{self.event_metadata.get('event_type_name')} ({self.event_metadata.get('event_type_slug')})\n"
        if self.user_data:
            description += f"With {self.user_data.get('resource', {}).get('name')}\n"
        description += "---\nQ&A:\n"
        for q in self.event_metadata.get("q_and_a", []):
            description += f"{q.get('question')}\n - {q.get('answer')}\n"
        description += self.get_description_additionals()
        description += (
            f"Location: {self.event_metadata.get('location')}\nEvent Kind: {self.event_metadata.get('event_kind')}"
        )
        return description

    def build_salesforce_payload(self):
        header = "Scheduled" if self.calendly_event_name == "invitee.created" else "Canceled"

        event_payload = {
            "salesforce_id": self.student_record.salesforce_id,
            "duration": self.event_metadata.get("event_duration"),
            "start_time": self.event_metadata.get("start_time"),
            "subject": f"{header}: {self.event_metadata.get('event_type_name')}",
            "description": self.create_description(),
            "type": "One-on-One" if self.calendly_event_name == "invitee.created" else "Meeting",
        }
        event_payload["assignee_id"] = self.calbright_user_id if self.calbright_user_id else None
        return event_payload

    # def store_event_in_database(self):
    #     print("TODO: Build out Event Data In The Database")

    def process_onboarding_session(self):
        email = self.student_record.calbright_email
        ccc_id = self.student_record.student.ccc_id
        learner_status = self.student_record.learner_status.status

        if not ccc_id or (
            learner_status not in ["App Submitted", "Started Orientation"]
            and self.event_metadata.get("event_type_uuid") != EventTypeUUID.CRM
        ):
            self.logger.warning(f"Invalid Data: learner_status={learner_status}, ccc_id={ccc_id} email={email}")
            return

        if self.event_metadata.get("event_type_uuid") == EventTypeUUID.CRM:
            self.update_learner_status("Ready for Onboarding")
        elif learner_status == "App Submitted":
            self.update_learner_status("Started Orientation")
            self.calbright.session.commit()
            self.update_learner_status("Completed Orientation")
        elif learner_status == "Started Orientation":
            self.update_learner_status("Completed Orientation")

        self.calbright.session.commit()
        return

    def get_description_additionals(self):
        dt = self.event_metadata.get("created_at")
        header = "Scheduled"
        closing = f"Text Reminder: {self.event_metadata.get('text_reminder_number')}\n"
        if self.calendly_event_name == "invitee.canceled":
            dt = self.event_metadata.get("cancelled_at")
            header = "Canceled"
            closing = f"Reason: {self.event_metadata.get('cancel_reason')}\n"

        return f"---\n{header} at: {convert_date_to_pst(dt)}\n{closing}"
