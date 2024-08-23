import unittest
from unittest.mock import Mock, MagicMock

from lambda_functions.calbright_trigger_workflow.workflow_system import WorkflowSystem
from src.exceptions import (
    UnknownPSQLTriggerType,
    MissingRequiredField,
)


class TestWorkflowSystem(unittest.TestCase):
    def setUp(self):
        self.ssm = MagicMock()
        self.configs = MagicMock()
        self.ws = WorkflowSystem(self.configs, self.ssm, "special_dlq_fifo")
        self.ws.dump_error_to_dlq = Mock(side_effect=self.mock_dump_error_to_dlq)
        self.dumped_to_dlq = False
        self.payload = {"psql_trigger_type": "new_ccc_application_trigger"}

    def test_required_attributes(self):
        for value in self.ws._psql_trigger_type_mapping.values():
            self.assertTrue(hasattr(value, "build"))
            self.assertTrue(hasattr(value, "process"))

    def test_unknown_psql_trigger_type_error(self):
        error_received = False
        try:
            self.ws.process_workflow(
                {
                    "psql_trigger_type": "bad_psql_trigger_type",
                    "id": "10000000-0000-0000-0000-100000000000",
                    "created_at": "2023-05-18 14:26:39.749475",
                    "trigger_op": "Some Operation",
                }
            )
        except UnknownPSQLTriggerType as err:
            error_received = True
            print(err)
            self.assertEqual(str(err), 'PSQL Trigger type "bad_psql_trigger_type" unrecognized')
        self.assertTrue(error_received)

    def test_required_fields(self):
        payload = self.payload
        for field in self.ws._required_fields:
            try:
                self.ws.process_workflow(self.payload)
            except MissingRequiredField as err:
                self.assertEqual(
                    str(err),
                    f'Workflow Trigger type "{payload.get("psql_trigger_type")}" is missing or size is 0 for the required field: {field}',  # noqa: E501
                )
            payload[field] = field

        self.assertTrue(self.dumped_to_dlq)

    def mock_dump_error_to_dlq(self, workflow_trigger_data):
        self.assertEqual(workflow_trigger_data, self.payload)
        self.dumped_to_dlq = True


if __name__ == "__main__":
    unittest.main()
