import os
import sys

sys.path.append(
    "/".join(
        os.path.dirname(os.path.realpath(__file__)).split("/")[:-1] + "lambda_functions/psql_trigger_handler".split("/")
    )
)
