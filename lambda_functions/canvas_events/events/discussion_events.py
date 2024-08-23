from propus.calbright_sql.calbright import Calbright
from propus.canvas import Canvas
from propus.salesforce import Salesforce
from events.base_event import BaseEvent


class DiscussionEntryCreatedEvent(BaseEvent):
    """
    This class is used to process the event of a discussion entry being created.
    https://canvas.instructure.com/doc/api/file.data_service_canvas_discussion.html
    """

    def __init__(self, event, psql_engine: Calbright, sf_client: Salesforce, canvas_client: Canvas):
        super().__init__(event, psql_engine, sf_client, canvas_client)

    def process(self):
        self.check_and_update_saa_timestamp()
        self.process_submission_event(lms_type="discussion")
        return True


class DiscussionEntrySubmittedEvent(BaseEvent):
    """
    This class is used to process the event of a discussion entry being submitted.
    https://canvas.instructure.com/doc/api/file.data_service_canvas_discussion.html
    """

    def __init__(self, event, psql_engine: Calbright, sf_client: Salesforce, canvas_client: Canvas):
        super().__init__(event, psql_engine, sf_client, canvas_client)

    def process(self):
        self.check_and_update_saa_timestamp()
        self.process_submission_event(lms_type="discussion")
        return True


class DiscussionTopicCreatedEvent(BaseEvent):
    """
    This class is used to process the event of a discussion topic being created.
    https://canvas.instructure.com/doc/api/file.data_service_canvas_discussion.html
    """

    def __init__(self, event, psql_engine: Calbright, sf_client: Salesforce, canvas_client: Canvas):
        super().__init__(event, psql_engine, sf_client, canvas_client)

    def process(self):
        self.check_and_update_saa_timestamp()
        return True


class DiscussionTopicUpdatedEvent(BaseEvent):
    """
    This class is used to process the event of a discussion topic being updated.
    https://canvas.instructure.com/doc/api/file.data_service_canvas_discussion.html
    """

    def __init__(self, event, psql_engine: Calbright, sf_client: Salesforce, canvas_client: Canvas):
        super().__init__(event, psql_engine, sf_client, canvas_client)

    def process(self):
        self.check_and_update_saa_timestamp()
        return True
