import unittest
from unittest.mock import Mock

import json

from lambda_functions.psql_trigger_handler.trigger_handler_system import TriggerHandlerSystem

from psql_src.exceptions import (
    UnknownTriggerType,
    MissingRequiredField,
)


class TestTriggerHandlerSystem(unittest.TestCase):
    def setUp(self):
        self.ws = TriggerHandlerSystem.build("some_environment")
        self.ws.sqs_queue = "some_test_sqs.fifo"
        self.ws.send_to_queue = Mock(side_effect=self.mock_send_message)
        self.mock_ran_sqs = False
        self.trigger_data = {
            "psql_trigger_type": "some_trigger_type",
            "id": "10000000-0000-0000-0000-100000000000",
            "created_at": "2023-05-18 14:26:39.749475",
        }

    def test_trigger_errors(self):
        with self.assertRaises(UnknownTriggerType):
            self.ws.process_trigger(
                {
                    "wrong_trigger": "bad_trigger_type",
                    "id": "10000000-0000-0000-0000-100000000000",
                    "created_at": "2023-05-18 14:26:39.749475",
                }
            )

        with self.assertRaises(MissingRequiredField):
            self.ws.process_trigger({"psql_trigger_type": "some_new_trigger", "no_id_field": "not an id"})

    def test_process_trigger(self):
        self.ws.process_trigger(self.trigger_data)
        self.assertTrue(self.mock_ran_sqs)

    def mock_send_message(self, trigger_payload):
        self.assertEqual(json.dumps(trigger_payload), json.dumps(self.trigger_data))
        self.mock_ran_sqs = True


if __name__ == "__main__":
    unittest.main()
