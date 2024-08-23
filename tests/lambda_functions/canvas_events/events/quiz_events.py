import unittest

from unittest.mock import MagicMock

from lambda_functions.canvas_events.canvas_event_system import CanvasEventSystem
from lambda_functions.canvas_events.events.quiz_events import QuizSubmittedEvent

from tests.lambda_functions.canvas_events.canvas_test_events import test_events

from tests.lambda_functions.canvas_events.services.mock_psql_services import create_mock_psql_services
from tests.lambda_functions.canvas_events.services.mock_sf_services import create_mock_sf_services
from tests.lambda_functions.canvas_events.services.mock_canvas_services import create_mock_canvas_services


class TestCanvasEventQuiz(unittest.TestCase):
    def setUp(self):
        self.psql_engine = create_mock_psql_services()
        self.sf_client = create_mock_sf_services()
        self.canvas_client = create_mock_canvas_services
        self.config = MagicMock()
        self.ces = CanvasEventSystem(
            config=self.config,
            psql_engine=self.psql_engine,
            sf_client=self.sf_client,
            canvas_client=self.canvas_client,
            dlq="canvas_events_test_dlq.fifo",
        )

    def test_quiz_submitted_event(self):
        test_event = test_events["quiz_submitted"]
        handler = QuizSubmittedEvent(
            event=test_event, psql_engine=self.psql_engine, sf_client=self.sf_client, canvas_client=self.canvas_client
        )
        handler.psql_services = self.psql_engine
        handler.sf_services = self.sf_client
        response = handler.process()
        self.assertTrue(response)


if __name__ == "__main__":
    unittest.main()
