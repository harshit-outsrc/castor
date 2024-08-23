#!/usr/bin/python3

import asyncio
import student_integrations.salesforce as salesforce
import student_integrations.process_sftp as process_sftp
from propus import Logging


def main():
    # Set Async Loop policy to avoid RuntimeError
    # Docker image setup
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) # Local windows setup
    logger = Logging.get_logger("castor/jobs/vcg_sftp_student_uploader/vcg_script")
    logger.info("Starting VCG Process.")

    # Get Student Information from Salesforce
    sfClient = asyncio.run(salesforce.login_salesforce())
    studentContactData = asyncio.run(salesforce.grab_student_contact_data(sfClient))
    studentAccountData = asyncio.run(salesforce.format_student_information(studentContactData))

    # Create CSV file and Upload to SFTP
    fileTitle = asyncio.run(process_sftp.create_CSV(studentAccountData))
    asyncio.run(process_sftp.process_file_and_upload_to_VCG(fileTitle))

    logger.info("Ending VCG Process.")


if __name__ == "__main__":
    main()
