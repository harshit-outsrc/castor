from typing import AnyStr, Dict

from propus.logging_utility import Logging

from psql_src.exceptions import UnknownTriggerType, MissingRequiredField


class TriggerHandlerSystem:
    _required_fields = ["id", "created_at"]

    def __init__(self, sqs_queue):
        self.logger = Logging.get_logger("castor/lambda_functions/psql_trigger_handler/trigger_handler_system")
        self.sqs_queue = sqs_queue
        self.fifo_message_attributes = {}

    @staticmethod
    def build(environment: AnyStr):
        """Build the Trigger Handler System based on environment provided

        Args:
            environment (string): The environment the system is suppose to run in. Ex. "dev", "stage", "prod"
        """

        queue = "localhost"
        if environment == "stage" or environment == "prod":
            queue = f"calbright_triggers_{environment}.fifo"

        return TriggerHandlerSystem(
            sqs_queue=queue,
        )

    @staticmethod
    def check_required_fields(psql_trigger: Dict, required_fields: set):
        """Validate trigger has required fields

        Args:
            psql_trigger (Dict): Dict of the data that was passed from trigger firing
            required_fields (set): Set of fields to check against, validating required fields exist

        Raises:
            MissingRequiredField: Raise an error with missing required field
        """
        for field in required_fields:
            if len(psql_trigger.get(field, "")) == 0:
                raise MissingRequiredField(psql_trigger.get("psql_trigger_type"), field)

    def process_trigger(self, trigger_payload):
        """Process triggers that come in and send them to the proper SQS

        Args:
            trigger_payload (Dict): Data received from the trigger

        Raises:
            UnknownTriggerType: Raise an error where trigger couldn't be determined
        """
        if trigger_payload.get("psql_trigger_type") is None:
            self.logger.error(f"unrecognized trigger: {trigger_payload}")
            raise UnknownTriggerType(trigger_payload)

        self.check_required_fields(trigger_payload, self._required_fields)
        self.fifo_message_attributes = {
            "MessageGroupId": f'group-{trigger_payload.get("psql_trigger_type")}',
            "MessageDeduplicationId": f'm-{trigger_payload.get("psql_trigger_type")}-{trigger_payload.get("id")}',
        }
        self.send_to_queue(trigger_payload)
        self.logger.info("Finished processing Trigger.")

    def send_to_queue(self, psql_trigger):
        """Send trigger data to FIFO SQS

        Args:
            psql_trigger (Dict): Data received from the trigger
        """
        import json
        from propus.aws.sqs import AWS_SQS

        if self.sqs_queue == "localhost":
            self.logger.info("PSQL Trigger Handler processed and would have added to FIFO SQS")
        else:
            self.logger.info(f'sending trigger {psql_trigger.get("psql_trigger_type")} to SQS {self.sqs_queue}')
            sqs = AWS_SQS.build()
            sqs.send_message(
                queue_name=self.sqs_queue,
                message=json.dumps(psql_trigger),
                **self.fifo_message_attributes,
            )
