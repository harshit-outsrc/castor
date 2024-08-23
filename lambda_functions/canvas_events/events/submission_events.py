from propus.calbright_sql.calbright import Calbright
from propus.canvas import Canvas
from propus.salesforce import Salesforce
from events.base_event import BaseEvent


class SubmissionCreatedEvent(BaseEvent):
    """
    This class is for processing the submission created event.
    https://canvas.instructure.com/doc/api/file.data_service_canvas_submission.html
    """

    def __init__(self, event, psql_engine: Calbright, sf_client: Salesforce, canvas_client: Canvas):
        super().__init__(event, psql_engine, sf_client, canvas_client)

    def process(self):
        self.check_and_update_saa_timestamp()
        self.process_submission_event()
        return True


class SubmissionUpdatedEvent(BaseEvent):
    """
    This class is for processing the submission updated event.
    https://canvas.instructure.com/doc/api/file.data_service_canvas_submission.html
    """

    def __init__(self, event, psql_engine: Calbright, sf_client: Salesforce, canvas_client: Canvas):
        super().__init__(event, psql_engine, sf_client, canvas_client)

    def process(self):
        # Not currently being used.... This event happens simultaneously with the submission created event and
        # grade_change events.
        return True
