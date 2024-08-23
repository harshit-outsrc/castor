from propus.calbright_sql.calbright import Calbright
from propus.canvas import Canvas
from propus.salesforce import Salesforce

from events.base_event import BaseEvent


class QuizSubmittedEvent(BaseEvent):
    """
    This class is used to process quiz submission events for Canvas quizzes (not Skillways quizzes)
    https://canvas.instructure.com/doc/api/file.data_service_canvas_quiz.html
    """

    def __init__(self, event, psql_engine: Calbright, sf_client: Salesforce, canvas_client: Canvas):
        super().__init__(event, psql_engine, sf_client, canvas_client)

    def process(self):
        self.check_and_update_saa_timestamp()
        self.process_submission_event(lms_type="quiz")
        return True
