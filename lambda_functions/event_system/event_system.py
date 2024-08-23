from propus.aws.ssm import AWS_SSM
from propus.logging_utility import Logging

from events.calendly_event import CalendlyEvent
from events.csep_complete import CsepComplete
from events.salesforce import SalesforceEvent
from events.veteran_intake_complete import VeteranIntakeComplete
from events.document_download import DownloadDocumentEvent
from events.hubspot_form_submitted import HubspotFormSubmitted
from events.sp_term_certified import SpTermGradeCertified

from events.tangoe_event import TangoeEvent
from events.dpau_request import DPAURequest
from events.dpau_complete import DPAUComplete
from exceptions import UnknownEventType, EmptyEventData


class EventSystem:
    _event_type_mapping = {
        "calendly_event": CalendlyEvent,
        "csep_complete": CsepComplete,
        "dpau_complete": DPAUComplete,
        "salesforce_event": SalesforceEvent,
        "veterans_intake_complete": VeteranIntakeComplete,
        "document_download_event": DownloadDocumentEvent,
        "dpau_request": DPAURequest,
        "hubspot_forms_submission": HubspotFormSubmitted,
        "salesforce_event": SalesforceEvent,
        "sp_term_grade_certified": SpTermGradeCertified,
        "tangoe_event": TangoeEvent,
        "veterans_intake_complete": VeteranIntakeComplete,
    }
    _required_keys = ["calbright_email", "date_completed", "event_type"]

    def __init__(self, configs, event_type, ssm, dlq):
        self.logger = Logging.get_logger("castor/lambda_functions/event_system/event_system")
        if self._event_type_mapping.get(event_type) is None:
            self.logger.error(f"unrecognized event: {event_type}")
            raise UnknownEventType(event_type)
        self.configs = configs
        self.ssm = ssm
        self.dead_letter_queue = dlq

    @staticmethod
    def build(environment, event_type):
        from configurations.dev import dev_configs
        from configurations.stage import stage_configs
        from configurations.prod import prod_configs

        configs = dev_configs
        if environment == "stage":
            configs = stage_configs
        elif environment == "prod":
            configs = prod_configs

        return EventSystem(
            configs=configs,
            event_type=event_type,
            ssm=AWS_SSM.build(use_cache=True),
            dlq=f"calbright_events_{environment}_dlq",
        )

    def process_event(self, event_message):
        if event_message.get("event_data") is None:
            self.logger.error(f"event missing data for {event_message.get('event_type')}")
            raise EmptyEventData(event_message.get("event_type"))

        system = self._event_type_mapping.get(event_message.get("event_type")).build(configs=self.configs, ssm=self.ssm)
        self.logger.info(f"beginning processing event `{event_message.get('event_type')}`")
        try:
            system.run(event_message.get("event_data"))
        except Exception as err:
            import traceback

            self.logger.error(
                f"""exception raised while processing {event_message.get('event_type')}. error: {str(err)}
                {traceback.format_exc()}"""
            )
            self.dump_error_to_dlq(event_message)

    def dump_error_to_dlq(self, message_body):
        import json
        from propus.aws.sqs import AWS_SQS

        self.logger.info(f"sending error message to DLQ {self.dead_letter_queue}")
        sqs = AWS_SQS.build()
        sqs.send_message(queue_name=self.dead_letter_queue, message=json.dumps(message_body))
