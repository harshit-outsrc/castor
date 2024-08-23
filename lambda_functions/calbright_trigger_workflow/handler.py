try:
    import unzip_requirements  # noqa
except ImportError:
    pass

import os
import json

from workflow_system import WorkflowSystem


def run(event, context):
    if os.environ.get("PRINT_EVENT"):
        print(event)

    for record in event.get("Records"):
        ws = WorkflowSystem.build(os.environ.get("ENV"))
        ws.process_workflow(json.loads(record.get("body")))


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 1:
        print("DEBUG: Please supply argument for running trigger workflow")

    if sys.argv[1] == "dlq":
        from propus.aws.sqs import AWS_SQS

        sqs = AWS_SQS.build()
        msg_req = sqs.receive_messages(sys.argv[2], visibility=60)
        env = os.environ.get("ENV")
        if env == "local":
            env = "dev"
        while len(msg_req.get("Messages", [])):
            for msg in msg_req.get("Messages"):
                message_body = json.loads(msg.get("Body"))
                ws = WorkflowSystem.build(env)
                ws.process_workflow(message_body)
                sqs.delete_message(sys.argv[2], msg.get("ReceiptHandle"))
            msg_req = sqs.receive_messages(sys.argv[2])
    elif sys.argv[1] == "test":
        test_trigger_data = {
            "Records": [
                {
                    "body": '{"psql_trigger_type": "update_create_grade_trigger", "id": "ddc2288a-aaa8-4162-953a-1064a57be910", "created_at": "2024-07-17 22:37:08", "trigger_op": "INSERT"}',  # noqa: E501
                }
            ]
        }
        run(test_trigger_data, None)
