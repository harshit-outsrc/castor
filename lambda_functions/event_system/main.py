try:
    import unzip_requirements  # noqa
except ImportError:
    pass

import os
import json

from event_system import EventSystem


def run(event, _):
    # This is only for debug events so they will show up in Cloudwatch
    if os.environ.get("PRINT_EVENT"):
        print(event)

    for record in event.get("Records"):
        event_body = json.loads(record.get("body"))
        es = EventSystem.build(os.environ.get("ENV"), event_body.get("event_type"))
        es.process_event(event_body)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 1:
        print("DEBUG: Please supply argument on what test event you would like to run")

    if sys.argv[1] == "csep_complete":
        from test_events.csep_complete import anthology_test as test_event
    elif sys.argv[1] == "veterans_intake_form_complete":
        from test_events.veterans_intake_form_completed import test_event
    elif sys.argv[1] == "tangoe_event":
        from test_events.tangoe_event import test_event
    elif sys.argv[1] == "hubspot_forms_submission":
        from test_events.hubspot_form_event import sample_data_enroll as test_event
    elif sys.argv[1] == "dpau_request":
        from test_events.dpau_request import dpau_form_submitted as test_event
    elif sys.argv[1] == "dpau_complete":
        from test_events.dpau_complete import dpau_complete as test_event
    elif sys.argv[1] == "calendly_event":
        """
        Calendly has many different events possible. Please see the calendly_events file. Here are additional
        imports you may use:

        # tests if the event membership user (Calbright Employee) is not in salesforce
        from test_events.calendly_events import no_user_in_salesforce

        # tests if the event scheduler is not in Salesforce
        from test_events.calendly_events import no_contact_record_in_salesforce

        # tests if the event event is created successfully with an attendee
        from test_events.calendly_events import invitee_created_success

        # tests if the event is scheduled with a user whom is not a student services or counselor employee
        from test_events.calendly_events import event_with_non_ss_or_counselor

        """
        from test_events.calendly_events import onboarding_sesison_da as test_event
    elif sys.argv[1] == "sp_term_event":
        from test_events.sp_term_certified_event import test_event

    if sys.argv[1] == "dlq":
        from propus.aws.sqs import AWS_SQS

        sqs = AWS_SQS.build()
        msg_req = sqs.receive_messages(sys.argv[2], visibility=60)
        while len(msg_req.get("Messages", [])):
            for msg in msg_req.get("Messages"):
                event_body = json.loads(msg.get("Body"))
                es = EventSystem.build(os.environ.get("ENV"), event_body.get("event_type"))
                es.process_event(event_body)
                sqs.delete_message(sys.argv[2], msg.get("ReceiptHandle"))
            msg_req = sqs.receive_messages(sys.argv[2])
    else:
        run(test_event, None)
