import os

from propus.aws.sqs import AWS_SQS
from propus.calbright_sql.calbright import Calbright
from propus.canvas import Canvas
from propus.salesforce import Salesforce
from propus.aws.ssm import AWS_SSM
from propus.logging_utility import Logging


class base_config(object):
    def __init__(self):
        self.logger = Logging.get_logger("castor/lambda_functions/canvas_events/configuration/config.py")

    def setup_sqs(self):
        """
        Setup the SQS client
        Returns: an SQS client

        """
        return AWS_SQS.build()

    def setup_postgres_engine(self, environment, ssm: AWS_SSM):
        """
        Setup the Postgres engine.
        If the environment is localhost, the credentials are pulled from the environment variables.
        Args:
            environment: a string representing the environment (e.g. "localhost", "staging", "prod")

        Returns: a Calbright object

        """
        try:
            if environment == "localhost":
                return Calbright.build(
                    {
                        "db": os.environ.get("DB"),
                        "host": "localhost",
                        "user": os.environ.get("USER"),
                        "password": os.environ.get("PASSWORD"),
                    },
                    verbose=False,
                )
            return Calbright.build(ssm.get_param(f"psql.calbright.{environment}.write", "json"))
        except Exception as err:
            self.logger.error(f" - Error during create_postgres_engine: {err}")
            raise err

    def setup_salesforce_client(self, environment, ssm: AWS_SSM):
        """
        Setup the Salesforce client.
        Args:
            environment: a string representing the environment (e.g. "localhost", "staging", "prod")

        Returns: a Salesforce object

        """
        return Salesforce.build_v2("prod" if environment == "prod" else "stage", ssm)

    def setup_canvas_client(self, environment, ssm: AWS_SSM):
        """
        Setup the Canvas client.
        Args:
            environment: a string representing the environment (e.g. "localhost", "staging", "prod")

        Returns: a Canvas object

        """

        canvas_creds = ssm.get_param(
            "canvas.dev.token" if environment == "localhost" else f"canvas.{environment}.token", param_type="json"
        )
        return Canvas(
            base_url=canvas_creds["base_url"],
            application_key=canvas_creds["token"],
            auth_providers=canvas_creds["auth_providers"],
        )
