import unittest
from unittest.mock import patch, MagicMock


from lambda_functions.canvas_events.canvas_event_system import CanvasEventSystem

# from lambda_functions.canvas_events.src.exceptions import UnknownCanvasEventType


# from tests.lambda_functions.canvas_events.canvas_test_events import test_events
from tests.lambda_functions.canvas_events.services.mock_psql_services import create_mock_psql_services
from tests.lambda_functions.canvas_events.services.mock_sf_services import create_mock_sf_services
from tests.lambda_functions.canvas_events.services.mock_canvas_services import create_mock_canvas_services
from tests.lambda_functions.canvas_events.services.mock_ssm import create_mock_ssm


class TestCanvasEventSystem(unittest.TestCase):

    @patch("lambda_functions.canvas_events.canvas_event_system.AWS_SSM.build")
    def setUp(self, mock_ssm_build):
        self.config = MagicMock()
        self.mock_ssm = create_mock_ssm()
        self.psql_engine = create_mock_psql_services()
        self.sf_client = create_mock_sf_services()
        self.canvas_client = create_mock_canvas_services()
        self.dlq = "canvas_events_test_dlq.fifo"

        mock_ssm_build.return_value = self.mock_ssm

        self.ces = CanvasEventSystem(
            config=self.config,
            psql_engine=self.psql_engine,
            sf_client=self.sf_client,
            canvas_client=self.canvas_client,
            dlq=self.dlq,
        )

    def test_initialization(self):
        self.assertEqual(self.ces.config, self.config)
        self.assertEqual(self.ces.psql_engine, self.psql_engine)
        self.assertEqual(self.ces.sf_client, self.sf_client)
        self.assertEqual(self.ces.canvas_client, self.canvas_client)
        self.assertEqual(self.ces.dlq, self.dlq)
        self.assertIn("asset_accessed", self.ces._event_type_mapping)

    def test_get_event_type(self):
        event = {"metadata": {"event_name": "asset_accessed"}}
        event_type = self.ces._get_event_type(event)
        self.assertEqual(event_type, "asset_accessed")

    # TODO: This was working before the `BaseTestClass` refactor - need to fix.
    #    I think the BaseTestClass is eating up the error instead of letting it propagate
    # def test_process_unknown_event(self):
    #     test_event = {
    #         "metadata": {"event_name": "unknown_event"},
    #         "body": {"key": "value"},
    #     }
    #     with self.assertRaises(UnknownCanvasEventType):
    #         self.ces.process_event(test_event)

    #
    @patch("lambda_functions.canvas_events.canvas_event_system.AWS_SSM.build", return_value=create_mock_ssm())
    def test_build(self, mock_ssm_build):
        environment = "test"
        with patch("lambda_functions.canvas_events.configuration.config.base_config") as mock_base_config, patch.object(
            mock_base_config.return_value, "setup_postgres_engine", return_value=self.psql_engine
        ), patch.object(
            mock_base_config.return_value, "setup_salesforce_client", return_value=self.sf_client
        ), patch.object(
            mock_base_config.return_value, "setup_canvas_client", return_value=self.canvas_client
        ):
            ces = CanvasEventSystem.build(environment)
            self.assertIsInstance(ces, CanvasEventSystem)
            self.assertEqual(ces.dlq, f"canvas_events_{environment}_dlq.fifo")


if __name__ == "__main__":
    unittest.main()
