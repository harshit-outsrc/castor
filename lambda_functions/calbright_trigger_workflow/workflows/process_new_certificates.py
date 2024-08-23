import asyncio
from typing import AnyStr

from propus.anthology import Anthology
from propus.calbright_sql.calbright import Calbright
from propus.logging_utility import Logging


class NewCertificates:

    def __init__(self, configs, psql_engine: Calbright, anthology: Anthology):
        self.configs = configs
        self.logger = Logging.get_logger(
            "castor/lambda_functions/calbright_trigger_workflow/workflows/process_new_certificates"
        )
        self.psql_engine = psql_engine
        self.anthology = anthology

        self.enrollment_record = Calbright.Enrollment

    @staticmethod
    def build(configs, ssm):
        from configuration.config import setup_anthology, setup_postgres_engine

        return NewCertificates(
            configs=configs,
            psql_engine=setup_postgres_engine(configs.get("psql_ssm"), ssm),
            anthology=setup_anthology(configs.get("anthology_ssm"), ssm),
        )

    def process(self, record_id: AnyStr, trigger_op: AnyStr):
        """ingestion process for new and existing grades that need to be processed and inserted into SIS (Anthology).

        Args:
            record_id (AnyStr): record id that needs to be ingested
            trigger_op (AnyStr): operation that fired trigger

        Raises:
            err: Log and raise error if new certificates workflow failed
        """
        try:
            if trigger_op == "INSERT" or trigger_op == "UPDATE":
                self.create_sis_certificates(record_id)

        except Exception as err:
            self.logger.error(f"Error during new_enrollment inserted: {err}")
            raise err

    def create_sis_certificates(self, record_id):
        """Create certificate on enrollment completion in SIS Anthology

        Args:
            record_id (str): record id that needs to be ingested

        Raises:
            err: Error raised if there are problems during the creation of certificate process in SIS (Anthology)
        """

        try:
            self.enrollment_record = (
                self.psql_engine.session.query(Calbright.Enrollment).filter_by(id=record_id).first()
            )

            asyncio.run(
                self.anthology.create_certificate(
                    self.enrollment_record.sis_enrollment_id,
                    self.enrollment_record.program_version.program.program_name,
                    self.enrollment_record.completion_date,
                )
            )

        except Exception as err:
            self.logger.error(f"Error during creation of certificate in Anthology: {err}")
            raise err

        return
