from typing import AnyStr, Dict

from propus.logging_utility import Logging

from src.exceptions import UnknownPSQLTriggerType, MissingRequiredField
from workflows.process_new_ccc_applications import NewCCCApplications
from workflows.process_new_enrollment import NewEnrollment
from workflows.process_update_create_grades import UpdateCreateGrades
from workflows.process_new_certificates import NewCertificates
from workflows.process_update_student_demographic import UpdateStudentDemographic


class WorkflowSystem:
    _psql_trigger_type_mapping = {
        "new_ccc_application_trigger": NewCCCApplications,
        "new_enrollment_trigger": NewEnrollment,
        "new_certificate_trigger": NewCertificates,
        "update_create_grade_trigger": UpdateCreateGrades,
        "update_student_demographic_trigger": UpdateStudentDemographic,
    }
    _required_fields = ["id", "created_at", "trigger_op"]

    def __init__(self, configs, ssm, dlq):
        self.configs = configs
        self.logger = Logging.get_logger("castor/lambda_functions/calbright_trigger_workflow/workflow_system")
        self.ssm = ssm
        self.dlq = dlq

    @staticmethod
    def build(environment: AnyStr):
        from propus.aws.ssm import AWS_SSM
        from configuration.dev import dev_configs
        from configuration.stage import stage_configs
        from configuration.prod import prod_configs

        configs = dev_configs
        if environment == "stage":
            configs = stage_configs
        elif environment == "prod":
            configs = prod_configs

        return WorkflowSystem(
            configs=configs,
            ssm=AWS_SSM.build("us-west-2", True),
            dlq=configs.get("dlq_ssm"),
        )

    @staticmethod
    def check_required_fields(psql_trigger_type: AnyStr, workflow_trigger: Dict, required_fields: set):
        for field in required_fields:
            if len(workflow_trigger.get(field, "")) == 0:
                raise MissingRequiredField(psql_trigger_type, field)

    def process_workflow(self, workflow_trigger):
        if self._psql_trigger_type_mapping.get(workflow_trigger.get("psql_trigger_type")) is None:
            self.logger.error(
                f"Unrecognized workflow trigger: {workflow_trigger.get('psql_trigger_type')}."
                f" full trigger: {workflow_trigger}"
            )
            raise UnknownPSQLTriggerType(workflow_trigger.get("psql_trigger_type"))

        try:
            self.check_required_fields(
                workflow_trigger.get("psql_trigger_type"), workflow_trigger, self._required_fields
            )

            system = self._psql_trigger_type_mapping.get(workflow_trigger.get("psql_trigger_type")).build(
                configs=self.configs, ssm=self.ssm
            )
            self.logger.info(f"New Workflow Trigger being processed: `{workflow_trigger.get('psql_trigger_type')}`")
            system.process(workflow_trigger.get("id"), workflow_trigger.get("trigger_op"))
            self.logger.info("Finished processing Workflow Trigger.")
        except Exception as err:
            import traceback

            self.logger.error(
                f"""exception raised while processing {workflow_trigger.get('psql_trigger_type')}. error: {err}
                {traceback.format_exc()}"""
            )
            self.dump_error_to_dlq(workflow_trigger)

    def dump_error_to_dlq(self, workflow_trigger_data):
        """Send trigger data to DLQ if any errors pop up that would prevent going to FIFO

        Args:
            psql_trigger (Dict): Data received from the trigger
        """
        import json
        from propus.aws.sqs import AWS_SQS

        if self.dlq == "localhost":
            self.logger.info("Error: Workflow didn't process and would get dropped on DLQ")
        else:
            deduplication_fields = {
                "MessageGroupId": f'group-{workflow_trigger_data.get("psql_trigger_type")}',
                "MessageDeduplicationId": f'm-{workflow_trigger_data.get("psql_trigger_type")}-{workflow_trigger_data.get("id")}',  # noqa: E501
            }
            self.logger.info(f"sending error message to DLQ {self.dlq}")
            sqs = AWS_SQS.build()
            sqs.send_message(queue_name=self.dlq, message=json.dumps(workflow_trigger_data), **deduplication_fields)
