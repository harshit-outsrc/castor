from typing import Optional

from src.exceptions import UnknownCanvasEventType


from events.asset_events import AssetAccessedEvent
from events.conversation_events import (
    ConversationCreatedEvent,
    ConversationMessageCreatedEvent,
)
from events.course_events import CourseCompletedEvent, CourseProgressEvent
from events.discussion_events import (
    DiscussionEntryCreatedEvent,
    DiscussionEntrySubmittedEvent,
    DiscussionTopicCreatedEvent,
    DiscussionTopicUpdatedEvent,
)
from events.submission_events import SubmissionCreatedEvent, SubmissionUpdatedEvent
from events.quiz_events import QuizSubmittedEvent
from events.grade_events import GradeChangeEvent

from events.logged_events import LoggedInEvent
from propus.aws.ssm import AWS_SSM
from propus.logging_utility import Logging


class CanvasEventSystem:
    """
    This class is responsible for processing the incoming events from the Canvas event system.
    It will determine the type of event and call the appropriate handler to process the event.
    """

    def __init__(self, config, psql_engine, sf_client, dlq, canvas_client):
        self.config = config
        self.logger = Logging.get_logger("castor/lambda_functions/canvas_events/canvas_event_system", debug=True)
        self.psql_engine = psql_engine
        self.sf_client = sf_client
        self.canvas_client = canvas_client
        self.dlq = dlq
        self._event_type_mapping = {
            "asset_accessed": AssetAccessedEvent,
            "discussion_entry_created": DiscussionEntryCreatedEvent,
            "discussion_entry_submitted": DiscussionEntrySubmittedEvent,
            "discussion_topic_created": DiscussionTopicCreatedEvent,
            "discussion_topic_updated": DiscussionTopicUpdatedEvent,
            "submission_created": SubmissionCreatedEvent,
            "submission_updated": SubmissionUpdatedEvent,
            "conversation_created": ConversationCreatedEvent,
            "conversation_message_created": ConversationMessageCreatedEvent,
            "course_completed": CourseCompletedEvent,
            "course_progress": CourseProgressEvent,
            "quiz_submitted": QuizSubmittedEvent,
            "grade_change": GradeChangeEvent,
            "logged_in": LoggedInEvent,
        }

    @staticmethod
    def build(environment: Optional[str]):
        """
        Build the CanvasEventSystem object.
        Requires the environment to be passed in as an argument.
        Args:
            environment: a string representing the environment (e.g. "localhost", "staging", "prod")

        Returns: a CanvasEventSystem object

        """
        from configuration.config import base_config

        config = base_config()
        ssm = AWS_SSM.build("us-west-2", use_cache=True)
        return CanvasEventSystem(
            config=config,
            psql_engine=config.setup_postgres_engine(environment, ssm),
            sf_client=config.setup_salesforce_client(environment, ssm),
            canvas_client=config.setup_canvas_client(environment, ssm),
            dlq=f"canvas_events_{environment}_dlq.fifo",
        )

    @staticmethod
    def _get_event_type(event):
        """
        Get the event type from the event metadata.
        Args:
            event: the event to get the type from

        Returns: a string representing the event type

        """
        return event.get("metadata").get("event_name")

    def process_event(self, event):
        """
        Process the event by determining the event type and calling the appropriate handler
        Args:
            event: the event to process

        Returns: None

        """
        event_type = self._get_event_type(event)
        if not self._event_type_mapping.get(event_type):
            self.logger.error(f"unrecognized event type: {event_type}. full event: {event}")
            raise UnknownCanvasEventType(event_type)
        handler = self._event_type_mapping.get(event_type)(
            event=event, psql_engine=self.psql_engine, sf_client=self.sf_client, canvas_client=self.canvas_client
        )
        self.logger.info(f"processing event of type {event_type}")
        handler.process()
