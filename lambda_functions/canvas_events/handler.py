try:
    import unzip_requirements  # noqa
except ImportError:
    pass

import json
import os
import traceback

from canvas_event_system import CanvasEventSystem
from src.exceptions import (
    AssigmentNotFoundInDatabase,
    UserNotFoundInDatabase,
    NoUserInfoInEvent,
    UnknownCanvasEventType,
)
from test_events import test_events


def run(event, _):
    """
    This is the entry point for the lambda function.
    Args:
        event: An SQS event from the Canvas events queue. Will be in the format of one of the Canvas events found
            here: https://canvas.instructure.com/doc/api/file.data_service_introduction.html
    Returns:

    """
    print(event)
    for record in event.get("Records"):
        event_body = json.loads(record.get("body"))
        ces = CanvasEventSystem.build(os.environ.get("ENV"))
        ces.process_event(event_body)


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "dlq":
        print("Running DLQ")
        from propus.aws.sqs import AWS_SQS

        sqs = AWS_SQS.build()
        msg_req = sqs.receive_messages(sys.argv[2], visibility=60)
        while len(msg_req.get("Messages", [])):
            for msg in msg_req.get("Messages"):
                try:
                    event_body = json.loads(msg.get("Body"))
                    print(event_body)
                    ces = CanvasEventSystem.build(os.environ.get("ENV"))
                    ces.process_event(event_body)
                    sqs.delete_message(sys.argv[2], msg.get("ReceiptHandle"))
                except (AssigmentNotFoundInDatabase, UserNotFoundInDatabase, NoUserInfoInEvent, UnknownCanvasEventType):
                    traceback.print_exc()
                    sqs.delete_message(sys.argv[2], msg.get("ReceiptHandle"))
                    continue

            msg_req = sqs.receive_messages(sys.argv[2])

    else:

        def create_test_sqs_event(event_body_dict):
            sqs_event = {
                "Records": [
                    {
                        "body": json.dumps(event_body_dict),
                    }
                ]
            }
            return sqs_event

        print("Running test events...")
        print(f"{len(test_events)} test events found")
        """
        These are some example events that can be used to test the lambda function locally.
        To use them, simply uncomment the event you want to test below and run the script.
        Note: not all events are implemented yet.
        """

        run(create_test_sqs_event(test_events["grade_change"]), None)
        # run(create_test_sqs_event(test_events["submission_created"]), None)

        # run(create_test_sqs_event(test_events["asset_accessed"]), None)
        # run(create_test_sqs_event(test_events["discussion_topic_created"]), None)
        # run(create_test_sqs_event(test_events["discussion_topic_updated"]), None)
        # run(create_test_sqs_event(test_events["discussion_entry_submitted"]), None)
        # run(create_test_sqs_event(test_events["discussion_entry_created"]), None)
        # run(create_test_sqs_event(test_events["conversation_message_created"]), None)
        # run(create_test_sqs_event(test_events["conversation_created"]), None)
        # run(create_test_sqs_event(test_events["quiz_submitted"]), None)
        # run(create_test_sqs_event(test_events["logged_in"]), None)

        # Not implemented yet or not going to be using for initial rollout...
        # run(create_test_sqs_event(test_events["course_completed"]), None)
        # run(create_test_sqs_event(test_events["course_progress"]), None)
        # run(create_test_sqs_event(test_events["submission_updated"]), None)
        # run(create_test_sqs_event(test_events['course_grade_change']), None)
        # run(create_test_sqs_event(test_events['grade_override']), None)
