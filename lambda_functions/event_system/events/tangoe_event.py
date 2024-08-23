import os
from propus.logging_utility import Logging
from events.base import BaseEventSystem
from events.constants import TANGOE_IDS
from exceptions import TangoePersonCreationError, TangoeActivityCreationError, TangoeActivityReturnError


class TangoeEvent(BaseEventSystem):
    __event_type__ = "tangoe_event"

    _required_fields = [
        "student_info",
        "event_timestamp",
    ]

    _student_info_fields = []

    def __init__(self, salesforce, gsheets, slack, geolocator, tangoemobile, tangoepeople):
        self.logger = Logging.get_logger("castor/lambda_functions/event_system/event/tangoe_event")
        self.salesforce = salesforce
        self.gsheets = gsheets
        self.slack = slack
        self.geolocator = geolocator
        self.address = ""
        self.tangoemobile = tangoemobile
        self.tangoepeople = tangoepeople
        self.test_channel = "automations-test"

    @staticmethod
    def build(configs, ssm):
        from services.salesforce_client import SalesforceService
        from services.gsheets_client import GoogleSheetsService
        from services.geolocator_client import GeolocatorClient
        from services.slack_client import SlackService
        from services.tangoe_client import TangoeMobileClient, TangoePeopleClient

        return TangoeEvent(
            salesforce=SalesforceService(configs.get("salesforce_ssm"), ssm),
            gsheets=GoogleSheetsService(configs.get("gsheets_svc_ssm"), ssm, configs.get("gsheets_keys")),
            slack=SlackService(configs.get("slack_ssm"), ssm),
            geolocator=GeolocatorClient(configs.get("geolocator_ssm"), ssm),
            tangoemobile=TangoeMobileClient(configs.get("tangoe_ssm"), ssm),
            tangoepeople=TangoePeopleClient(configs.get("tangoe_ssm"), ssm),
        )

    def send_device_request(self, student_info, event_timestamp):
        device_requests = dict()
        student = self.salesforce.get_student_devices_by_ccc_id(student_info.get("ccc_id"))
        student_info["cb_requested"] = (
            False if student.get("cfg_Chromebook_Requested__c") is True else student_info.get("cb_requested")
        )
        student_info["hs_requested"] = (
            False if student.get("cfg_Hotspot_Requested__c") is True else student_info.get("hs_requested")
        )

        person_exists = self.tangoemobile.get_user(student_info.get("ccc_id")) != {}

        if not person_exists:
            try:
                person_data = {
                    "person": {
                        "email": student_info.get("email"),
                        "employee_id": student_info.get("ccc_id"),
                        "group_id": TANGOE_IDS.get("group_id"),
                        "name_first": student_info.get("first_name"),
                        "name_last": student_info.get("last_name"),
                        "new_base_country_membership_country_id": (
                            TANGOE_IDS.get("new_base_country_membership_country_id")  # Country=US
                        ),
                        "shipping_address_attributes": {
                            "address1": student_info.get("street"),
                            "address2": student_info.get("address2"),
                            "city": student_info.get("city"),
                            "country_id": TANGOE_IDS.get("country_id"),
                            "ship_attention": f"{ student_info.get('first_name') } {student_info.get('last_name') }",
                            "state": student_info.get("state"),
                            "zip": student_info.get("zipcode"),
                        },
                    }
                }
                created = self.tangoepeople.create_user(person_data)
                if not created:
                    raise TangoePersonCreationError()
                if created.get("status") == "bad_request":
                    raise TangoePersonCreationError(",".join(created.get("message")))

            except Exception as e:
                self.logger.error(f"Error creating Tangoe Person for student {student_info.get('ccc_id')} :  {e}")
                raise TangoePersonCreationError(e)

        try:
            if student_info.get("cb_requested"):
                device_requests["cfg_Chromebook_Requested__c"] = student_info.get("cb_requested")
                self.tangoemobile.request_chromebook(self.get_request_payload(student_info, "Chromebook"))
                self.logger.info(f"Submitted chromebook request activity for {student_info.get('ccc_id')}")
            if student_info.get("hs_requested"):
                device_requests["cfg_Hotspot_Requested__c"] = student_info.get("hs_requested")
                self.tangoemobile.request_hotspot(self.get_request_payload(student_info, "Hotspot"))
                self.logger.info(f"Submitted hotspot request activity for {student_info.get('ccc_id')}")
        except Exception as e:
            self.logger.error(f"Error creating Tangoe Activity for student {student_info.get('ccc_id')} :  {e}")
            raise TangoeActivityCreationError(e)

        if device_requests:
            if student_info.get("device_requested_method") == "CSEP":
                device_requests["Device_Requested_on_CSEP__c"] = True

            self.salesforce.client.update_contact_record(
                student_info.get("id"),
                Device_Shipping_Address__c=student_info.get("address"),
                **device_requests,
            )
            self.gsheets.append_new_learner_device_request(
                **self.build_gsheets_row(student_info, event_timestamp),
                sheet_tab=self.gsheets.sheets_key_table.get("tangoe_requests_tab"),
            )
            self.slack.alert_admins_of_tangoe_device_requested(
                self.test_channel or "new-learner-device-log-admin", info=student_info
            )
            self.slack.alert_staff_of_device_added_to_gsheets_for_processing(
                self.test_channel or "new-learner-device-log", info=student_info
            )
        else:
            self.logger.info(f'Attempted Duplicate Device Request: {student_info.get("ccc_id")}.')
            self.slack.alert_staff_of_tangoe_duplicate_request(
                self.test_channel or "new-learner-device-log", info=student_info
            )

    def build_gsheets_row(self, student_info, timestamp):

        row = {
            "timestamp": timestamp,
            "cccid": student_info.get("ccc_id"),
            "email": student_info.get("email"),
            "first_name": student_info.get("first_name"),
            "last_name": student_info.get("last_name"),
            "phone": student_info.get("phone"),
            "shipping_address": student_info.get("address"),
            "include_chromebook": "Yes" if student_info.get("cb_requested") is True else "No",
            "include_hotspot": "Yes" if student_info.get("hs_requested") is True else "No",
            "policy_signed": "Yes" if student_info.get("policy_signed") is True else "No",
        }

        return row

    def get_request_payload(self, student_info, device):
        activity_type_id = ""
        if device == "Chromebook":
            activity_type_id = TANGOE_IDS.get("chromebook_activity_type_id")
        elif device == "Hotspot":
            activity_type_id = TANGOE_IDS.get("hotspot_activity_type_id")
        else:
            raise ValueError("Unsupported device type")

        business_ref_device_id = ""
        if device == "Chromebook":
            business_ref_device_id = TANGOE_IDS.get("chromebook_business_ref_device_id")
        elif device == "Hotspot":
            business_ref_device_id = TANGOE_IDS.get("hotspot_business_ref_device_id")
        else:
            raise ValueError("Unsupported device type")
        payload = {
            "activity": {
                "activity_type_id": activity_type_id,
                "employee_id": student_info.get("ccc_id"),
                "shipping_address_attributes": {
                    "address1": student_info.get("street"),
                    "address2": student_info.get("address2"),
                    "city": student_info.get("city"),
                    "country_id": TANGOE_IDS.get("country_id"),
                    "ship_attention": f"{ student_info.get('first_name') } {student_info.get('last_name') }",
                    "state": student_info.get("state"),
                    "zip": student_info.get("zipcode"),
                },
                "business_ref_device_id": business_ref_device_id,
            }
        }
        return payload

    def send_device_return(self, student_info, event_timestamp):
        device_return = dict()
        student = self.salesforce.get_student_devices_by_ccc_id(student_info.get("ccc_id"))
        student_info["cb_return"] = (
            False if student.get("cfg_Chromebook_Return__c") is True else student_info.get("cb_return")
        )
        student_info["hs_return"] = (
            False if student.get("cfg_Hotspot_Return__c") is True else student_info.get("hs_return")
        )
        try:
            line_resp = self.tangoemobile.get_lines(student_info.get("ccc_id"))
            line_id = line_resp['response'][0]['id']
            student_info["line_id"] = line_id
            student_info["return_tracking_number"] = 9999
            device_resp = self.tangoemobile.get_lines(student_info.get("ccc_id"))
            student_info["return_imei"] = ""
            student_info["return_generic_serial"] = ""
            for i in device_resp["response"]:
                student_info["return_generic_serial"] = i["generic_serial"]
                student_info["return_imei"] = i["imei"]
                if student_info["return_generic_serial"]:
                    if student_info.get("cb_return"):
                        device_return["cfg_Chromebook_Return__c"] = student_info.get("cb_return")
                        self.tangoe.return_chromebook(self.get_return_device_payload(student_info))
                if student_info["return_imei"]:
                    if student_info.get("hs_return"):
                        device_return["cfg_Hotspot_Return__c"] = student_info.get("hs_return")
                        self.tangoe.suspend_hotspot(self.get_suspend_hotspot_payload(student_info))
                        self.tangoe.return_hotspot(self.get_return_device_payload(student_info))
                student_info["return_imei"] = ""
                student_info["return_generic_serial"] = ""
        except Exception as e:
            self.logger.error(f"Error creating Tangoe Activity for student {student_info.get('ccc_id')} :  {e}")
            raise TangoeActivityReturnError(e)
        if device_return:
            self.salesforce.client.update_contact_record(
                student_info.get("id"),
                Device_Requested_on_CSEP__c=False,
                Device_Shipping_Address__c=student_info.get("address"),
                **device_return,
            )
            self.gsheets.append_new_learner_device_request(
                **self.build_gsheets_row(student_info, event_timestamp)
            )
            self.slack.alert_admins_of_device_return(
                self.test_channel or "new-learner-device-log-admin", info=student_info
            )
            self.slack.alert_staff_of_device_added_to_gsheets_for_processing(
                self.test_channel or "new-learner-device-log", info=student_info
            )
        else:
            self.logger.info(f'Attempted Duplicate Device Request: {student_info.get("ccc_id")}.')

    def get_suspend_hotspot_payload(self, student_info):
        payload = {
            "activity": {
                "activity_type_id": student_info.get("activity_type_id", ""),
                "line_id": student_info.get("line_id", None),
                "employee_id": student_info.get("employee_id", ""),
                "comment": student_info.get("comment", ""),
                "remote_activity_id": student_info.get("remote_activity_id", "the_remote_system_unique_id")
            }
        }
        return payload

    def get_return_device_payload(self, student_info):
        payload = {
            "activity": {
                "activity_type_id": student_info.get("activity_type_id", ""),
                "employee_id": student_info.get("employee_id", ""),
                "shipping_address_attributes": {
                    "address1": student_info.get("address1", ""),
                    "address2": student_info.get("address2", ""),
                    "city": student_info.get("city", ""),
                    "zip": student_info.get("zip", ""),
                    "country_id": student_info.get("country_id", None),
                    "state": student_info.get("state", ""),
                    "ship_attention": student_info.get("ship_attention", "")
                },
                "comment": student_info.get("comment", ""),
                "return_imei": student_info.get("return_imei", None),
                "return_generic_serial": student_info.get("return_generic_serial", ""),
                "return_tracking_number": student_info.get("return_tracking_number", ""),
                "return_courier_id": student_info.get("return_courier_id", None),
                "remote_activity_id": student_info.get("remote_activity_id", "the_remote_system_unique_id")
            }
        }
        return payload

    def format_shipping_address(self, street, city, state, zipcode):
        return f"{street}, {city}, {state} {zipcode}"

    @staticmethod
    def check_required_fields(event_type, event, required_fields: set):
        from exceptions import MissingRequiredField

        for field in required_fields:
            if field not in event:
                raise MissingRequiredField(event_type, field)

        student_info = [
            "id",
            "city",
            "state",
            "street",
            "zipcode",
            "device_requested_method",
            "device_agreement_sent_for_signature",
            "first_name",
            "last_name",
            "ccc_id",
            "email",
            "phone",
            "policy_signed",
            "cb_requested",
            "hs_requested",
            "cb_return",
            "hs_return"
        ]

        for field in student_info:
            if field not in event.get("student_info", {}):
                raise MissingRequiredField(event_type, field)

    def run(self, event_data):
        self.check_required_fields(self.__event_type__, event_data, self._required_fields)
        if os.environ.get("ENV") not in ("dev", "stage"):
            self.test_channel = None
        event_data["student_info"]["address"] = self.format_shipping_address(
            event_data.get("student_info").get("street"),
            event_data.get("student_info").get("city"),
            event_data.get("student_info").get("state"),
            event_data.get("student_info").get("zipcode"),
        )
        valid_address = self.geolocator.validate(event_data.get("student_info").get("address"))
        event_data["student_info"]["address_verification_status"] = (
            "Valid Address" if valid_address else "Invalid Address"
        )
        if valid_address:
            student_info = event_data.get("student_info")
            if student_info.get("device_requested_method") or student_info.get("device_agreement_sent_for_signature"):
                if student_info.get("cb_requested") or student_info.get("hs_requested"):
                    self.send_device_request(student_info, event_data.get("event_timestamp"))
                elif student_info.get("cb_return") or student_info.get("hs_return"):
                    self.send_device_return(student_info, event_data.get("event_timestamp"))
                elif student_info.get("cb_replace") or student_info.get("hs_replace"):
                    self.send_device_replace(student_info, event_data.get("event_timestamp"))
                elif student_info.get("cb_stolen") or student_info.get("hs_stolen"):
                    self.send_device_stolen(student_info, event_data.get("event_timestamp"))

        else:
            self.slack.alert_staff_of_shipping_address_failure(
                self.test_channel or "new-learner-device-log", info=event_data.get("student_info")
            )
            raise Exception(
                f"{event_data.get('student_info').get('ccc_id')}: Error determining address, status: {valid_address}."
            )
        return
