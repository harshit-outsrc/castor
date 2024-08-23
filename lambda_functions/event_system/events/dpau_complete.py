from datetime import datetime, timezone
import os
from typing import Dict

from propus.helpers.input_validations import validate_email
from propus.logging_utility import Logging
from events.base import BaseEventSystem


class DPAUComplete(BaseEventSystem):
    __event_type__ = "dpau_complete"

    _required_fields = ["id", "tokens", "date_modified", "fields"]
    _required_tokens = ["Student.CCCID", "Student.FullName"]

    _form_bucket = None

    def __init__(self, configs, salesforce, geolocator, sqs):
        super().__init__(configs)
        self.logger = Logging.get_logger("castor/lambda_functions/event_system/event/dpau_complete")
        self.salesforce = salesforce
        self.geolocator = geolocator
        self.sqs = sqs
        self.datetime_now = datetime.now(timezone.utc)  # Using UTC standard for other systems
        self.datetime_now_isoformat = self.datetime_now.isoformat()
        self._form_bucket = configs.get("form_bucket")

    @staticmethod
    def build(configs, ssm):
        from services.salesforce_client import SalesforceService
        from services.geolocator_client import GeolocatorClient
        from propus.aws.sqs import AWS_SQS

        return DPAUComplete(
            configs=configs,
            salesforce=SalesforceService(configs.get("salesforce_ssm"), ssm),
            geolocator=GeolocatorClient(configs.get("geolocator_ssm"), ssm),
            sqs=AWS_SQS.build(),
        )

    def run(self, event_data):
        try:
            student_tokens, student_record = self.validate_dpau_data(event_data)
            pd_requests = self.get_dpau_requests(event_data)
            self.logger.info(f"Grabbed DPAU Request for: {student_tokens.get('Student.CCCID')}.")
            student_address = self.geolocator.get(pd_requests.get("shipping_address"))
            shipping_address = f'{student_address.get("address1")} {student_address.get("address2")}, {student_address.get("city")}, {student_address.get("state")} {student_address.get("zip")}'  # noqa: E501

            student_data = {}
            student_data["address"] = student_address
            student_data["first_name"] = student_record.get("FirstName")
            student_data["last_name"] = student_record.get("LastName")
            student_data["phone_number"] = student_record.get("Phone")
            student_data["calbright_email"] = student_record.get("cfg_Calbright_Email__c")
            student_data["salesforce_id"] = student_record.get("Id")
            student_data["ccc_id"] = student_tokens.get("Student.CCCID")
            student_data["chromebook"] = pd_requests.get("chromebook")
            student_data["hotspot"] = pd_requests.get("hotspot")

            self.salesforce.client.update_contact_record(
                student_data.get("salesforce_id"),
                Device_Agreement_Signed_Date__c=event_data.get("date_modified"),
                Device_Shipping_Address__c=shipping_address,
            )

            if student_data.get("chromebook") or student_data.get("hotspot"):
                self.setup_tangoe_payload(student_data)

        except Exception as err:
            self.logger.error(f"Error on signed DPAU for {event_data.get('name')}: {err}")
            raise err

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
                    "street": f'{student_data.get("address").get("address1", "")} {student_data.get("address").get("address2", "")}',  # noqa: E501
                    "city": student_data.get("address").get("city", ""),
                    "state": student_data.get("address").get("state", ""),
                    "zipcode": student_data.get("address").get("zip", ""),
                    "device_requested_method": "Post-CSEP",
                    "device_agreement_sent_for_signature": None,
                    "ccc_id": student_data.get("ccc_id"),
                    "policy_signed": True,
                    "cb_requested": student_data.get("chromebook"),
                    "hs_requested": student_data.get("hotspot"),
                },
                "event_timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

        self.sqs.send_message(f'calbright_events_{os.environ.get("ENV")}', json.dumps(tangoe_data))
        self.logger.info(f'Created Device Request Event for: {student_data.get("calbright_email")}.')

    def validate_dpau_data(self, event_data: dict):
        """
        Validates the DPAU data received from an event.

        Args:
            self: The instance of the class containing this method.
            event_data (dict): A dictionary containing the event data, including tokens and fields.

        Returns:
            - sf_data (dict): A dictionary containing the student's Salesforce data, intended program, CRM status

        """
        tokens = {k: v for d in event_data.get("tokens") for k, v in d.items()}
        self.check_required_fields(self.__event_type__, tokens, self._required_tokens)

        validate_email(tokens.get("Student.CalbrightEmail"))
        sf_data = self.salesforce.get_student_devices_by_ccc_id(tokens.get("Student.CCCID"))

        return tokens, sf_data

    @staticmethod
    def get_dpau_requests(event_data: Dict) -> Dict:
        """
        Get the DPUA requests from the event data.
        :param event_data: The event data.
        :return: A dictionary of the DPUA requests.
        """
        fields = {field.get("field_id"): field for field in event_data.get("fields")}

        requests = {}
        for key, panda_key in {
            "shipping_address": "ShippingAddress",
            "chromebook": "chromebook_checked",
            "hotspot": "hotspot_checked",
        }.items():
            requests[key] = fields.get(panda_key, {}).get("value") if fields.get(panda_key, {}).get("value") else False

        return requests
