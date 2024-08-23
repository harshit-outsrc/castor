from propus.calbright_sql.calbright import Calbright
from propus.canvas import Canvas
from propus.salesforce import Salesforce
from events.base_event import BaseEvent


class ConversationCreatedEvent(BaseEvent):
    """
    This class processes the conversation_created event from Canvas.
    https://canvas.instructure.com/doc/api/file.data_service_canvas_conversation.html
    """

    def __init__(self, event, psql_engine: Calbright, sf_client: Salesforce, canvas_client: Canvas):
        super().__init__(event, psql_engine, sf_client, canvas_client)

    def process(self):
        return self.process_non_saa_activity_event(activity_type="conversation")


class ConversationMessageCreatedEvent(BaseEvent):
    """
    This class processes the conversation_message_created event from Canvas.
    https://canvas.instructure.com/doc/api/file.data_service_canvas_conversation.html
    """

    def __init__(self, event, psql_engine: Calbright, sf_client: Salesforce, canvas_client: Canvas):
        super().__init__(event, psql_engine, sf_client, canvas_client)

    def process(self):
        return self.process_non_saa_activity_event(activity_type="conversation")
