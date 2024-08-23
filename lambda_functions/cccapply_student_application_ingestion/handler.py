import src.process_oracle as process_oracle
import src.process_postgres as process_postgres
from propus.logging_utility import Logging


def run(event, context):
    logger = Logging.get_logger("castor/lambda_functions/cccapply_student_application_ingestion")

    calbright_oracle = process_oracle.CCCApplyOracleDB()
    calbright_oracle.query_student_applications_for_ingestion()

    if calbright_oracle.new_student_applicants_exist:
        logger.info(f" - Found {len(calbright_oracle.student_records)} Student Records for ingestion")
        calbright_postgres = process_postgres.CalbrightPSQL()
        calbright_postgres.ingest_student_applications(calbright_oracle.student_records)
        calbright_oracle.finish_processing_ingested_records()
        logger.info(" - Finished CCCApply Student Application Ingestion")


if __name__ == "__main__":
    run(None, None)
