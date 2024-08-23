from propus.calbright_sql.calbright import Calbright
from propus.canvas import Canvas
from propus.salesforce import Salesforce

from events.base_event import BaseEvent


class GradeChangeEvent(BaseEvent):
    """
    This class is used to process grade change events from Canvas.
    https://canvas.instructure.com/doc/api/file.data_service_canvas_grade.html
    """

    def __init__(self, event, psql_engine: Calbright, sf_client: Salesforce, canvas_client: Canvas):
        super().__init__(event, psql_engine, sf_client, canvas_client)

    def process(self):
        self.process_grade_change_event()
        return True
