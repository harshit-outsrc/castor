try:
    import unzip_requirements  # noqa
except ImportError:
    pass

import os
from trigger_handler_system import TriggerHandlerSystem


def run(event, context):
    ths = TriggerHandlerSystem.build(os.environ.get("ENV"))
    ths.process_trigger(event)


if __name__ == "__main__":
    # Testing Purposes
    run(
        {
            "psql_trigger_type": "new_ccc_application_trigger",
            "id": "10000000-0000-0000-0000-100000000000",
            "created_at": "2023-05-19 13:51:23.212586",
        },
        None,
    )
