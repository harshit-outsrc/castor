import os
import time
from datetime import datetime, timezone

from propus.helpers.input_validations import validate_email
from propus.logging_utility import Logging

from events.base import BaseEventSystem
from events.constants import PANDADOC_TEMPLATES
from exceptions import PandaDocCreationError


class DPAURequest(BaseEventSystem):
    __event_type__ = "dpau_request"
    _required_fields = [
        "form_id",
        "response_id",
        "dpau_form_submitted",
        "ccc_id",
        "calbright_email",
        "chromebook",
        "hotspot",
        "street",
        "city",
        "state",
        "zipcode",
    ]

    def __init__(self, configs, salesforce, pandadoc, geolocator, slack, sqs):
        super().__init__(configs)
        self.logger = Logging.get_logger("castor/lambda_functions/event_system/event/dpau_request")
        self.salesforce = salesforce
        self.pandadoc = pandadoc
        self.geolocator = geolocator
        self.slack = slack
        self.sqs = sqs
        self.slack_channel = "automations-test"

    @staticmethod
    def build(configs, ssm):
        from services.salesforce_client import SalesforceService
        from services.pandadoc_client import PandaDocClient
        from services.geolocator_client import GeolocatorClient
        from services.slack_client import SlackService
        from propus.aws.sqs import AWS_SQS

        return DPAURequest(
            configs=configs,
            salesforce=SalesforceService(configs.get("salesforce_ssm"), ssm),
            pandadoc=PandaDocClient(configs.get("pandadoc_ssm"), ssm),
            geolocator=GeolocatorClient(configs.get("geolocator_ssm"), ssm),
            slack=SlackService(configs.get("slack_ssm"), ssm),
            sqs=AWS_SQS.build(),
        )

    def run(self, event_data):
        if os.environ.get("ENV") not in ("dev", "stage"):
            self.slack_channel = "new-learner-device-log"

        self.check_required_fields(self.__event_type__, event_data, self._required_fields)

        validate_email(event_data.get("calbright_email"))
        shipping_address = f'{event_data.get("street")}, {event_data.get("city")}, {event_data.get("state")} {event_data.get("zipcode")}'  # noqa: E501
        valid_address = self.geolocator.validate(shipping_address)

        if valid_address:
            salesforce_record = self.salesforce.get_student_devices_by_ccc_id(event_data.get("ccc_id"))

            event_data["address"] = shipping_address
            event_data["first_name"] = salesforce_record.get("FirstName")
            event_data["last_name"] = salesforce_record.get("LastName")
            event_data["phone_number"] = salesforce_record.get("Phone")
            event_data["salesforce_id"] = salesforce_record.get("Id")
            event_data["calbright_email"] = salesforce_record.get("cfg_Calbright_Email__c")
            try:

                if salesforce_record.get("Device_Requested_on_CSEP__c") or salesforce_record.get(
                    "Device_Agreement_Signed_Date__c"
                ):
                    self.setup_tangoe_payload(event_data)
                else:
                    self.send_dpau_panda_doc(
                        template_id=PANDADOC_TEMPLATES.get("post_csep_dpau"),
                        student_data=event_data,
                        subject="Calbright Device Request Acceptable Use and Device Policies.",
                        message=f"Hi {event_data.get('first_name')}, You indicated interest in Calbright's Learner"
                        " Device program. Before we can mail you a device, you will need to read and agree to the"
                        " Acceptable Use Policy and the Computer & Device Policy by electronically signing the enclosed"
                        " document. Please contact your Academic Success Counselor if you have any questions.",
                    )
                    self.salesforce.client.update_contact_record(
                        event_data.get("salesforce_id"),
                        Device_Shipping_Address__c=shipping_address,
                        Device_Agreement_Sent_For_Signature_Date__c=datetime.now(timezone.utc).strftime(
                            "%Y-%m-%dT%H:%M:%S.000+0000"
                        ),
                    )
                    self.logger.info(f"Student sent DPAU and Salesforce updated for {event_data.get('ccc_id')}.")
            except Exception as err:
                self.logger.error(f"Error processing DPAU submission for student {event_data.get('ccc_id')}: {err}")
        else:
            event_data["address_verification_status"] = valid_address
            self.slack.alert_staff_of_shipping_address_failure(self.slack_channel, info=event_data)

    def setup_tangoe_payload(self, student_data):
        import json

        tangoe_data = {
            "event_type": "tangoe_event",
            "event_data": {
                "student_info": {
                    "first_name": student_data.get("first_name"),
                    "last_name": student_data.get("last_name"),
                    "phone": student_data.get("phone_number"),
                    "email": student_data.get("calbright_email"),
                    "id": student_data.get("salesforce_id"),
                    "street": student_data.get("street", ""),
                    "city": student_data.get("city", ""),
                    "state": student_data.get("state", ""),
                    "zipcode": student_data.get("zipcode", ""),
                    "device_requested_method": "Post-CSEP",
                    "device_agreement_sent_for_signature": None,
                    "ccc_id": student_data.get("ccc_id"),
                    "policy_signed": True,
                    "cb_requested": True if student_data.get("chromebook") == "Yes" else False,
                    "hs_requested": True if student_data.get("hotspot") == "Yes" else False,
                },
                "event_timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

        self.sqs.send_message(f'calbright_events_{os.environ.get("ENV")}', json.dumps(tangoe_data))
        self.logger.info(f'Created Device Request Event for: {student_data.get("calbright_email")}.')

    def send_dpau_panda_doc(self, template_id, student_data, subject, message):
        try:
            resp = self.pandadoc.create_document_from_template(
                template_id=template_id,
                email_name=student_data.get("calbright_email"),
                recipient_first_name=student_data.get("first_name"),
                recipient_last_name=student_data.get("last_name"),
                recipient_email=student_data.get("calbright_email"),
                tokens=[
                    {
                        "name": "Student.FullName",
                        "value": f'{student_data.get("first_name")} {student_data.get("last_name")}',
                    },
                    {"name": "Student.CCCID", "value": student_data.get("ccc_id")},
                ],
                fields=[
                    {"ShippingAddress": {"value": student_data.get("address")}},
                    {"chromebook_checked": {"value": True if student_data.get("chromebook") == "Yes" else False}},
                    {"hotspot_checked": {"value": True if student_data.get("hotspot") == "Yes" else False}},
                ],
            )
            time.sleep(5)
            self.pandadoc.send_document(
                doc_id=resp.get("id"),
                subject=subject,
                message=message,
            )
        except Exception as err:
            raise PandaDocCreationError(student_data.get("ccc_id"), err)
