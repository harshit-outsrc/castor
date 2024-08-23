import os
import sys

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append("/".join(current_path.split("/")[:-2] + "lambda_functions/canvas_events".split("/")))
from tests.lambda_functions.canvas_events.canvas_event_system_test import TestCanvasEventSystem
from tests.lambda_functions.canvas_events.events.asset_events import TestCanvasEventAsset
from tests.lambda_functions.canvas_events.events.conversation_events import TestCanvasEventConversation
from tests.lambda_functions.canvas_events.events.course_events import TestCanvasEventCourse
from tests.lambda_functions.canvas_events.events.discussion_events import TestCanvasEventDiscussion
from tests.lambda_functions.canvas_events.events.grade_events import TestCanvasEventGrade
from tests.lambda_functions.canvas_events.events.logged_events import TestCanvasEventLoggedIn
from tests.lambda_functions.canvas_events.events.quiz_events import TestCanvasEventQuiz
from tests.lambda_functions.canvas_events.events.submission_events import TestCanvasEventSubmission

from tests.start_scripts.base import BaseTestClass


class CanvasEventsTests(BaseTestClass):
    def __init__(self, test_name):
        super().__init__(test_name)

        self.tests = [
            TestCanvasEventAsset,
            TestCanvasEventConversation,
            TestCanvasEventCourse,
            TestCanvasEventDiscussion,
            TestCanvasEventGrade,
            TestCanvasEventLoggedIn,
            TestCanvasEventQuiz,
            TestCanvasEventSubmission,
            TestCanvasEventSystem,
        ]


if __name__ == "__main__":
    CanvasEventsTests("canvas_events").run()
