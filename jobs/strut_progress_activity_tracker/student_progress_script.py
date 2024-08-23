#!/usr/bin/python3

import asyncio
import time
import student_integrations.salesforce as salesforce
import student_integrations.strut as strut
from propus.logging_utility import Logging

# from datetime import datetime, timezone


def main():
    # Set Async Loop policy to avoid RuntimeError

    # Docker image setup
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    logger = Logging.get_logger("castor/jobs/strut_progress_activity_tracker/student_progress_script")

    # Local windows setup
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # logging.basicConfig(filename='C:/Users/15102/Documents/GitHub/castor/jobs/strut_progress_activity_tracker/logs/student_progress.log', filemode='w', level=logging.INFO, format='%(asctime)s - %(filename)s - %(levelname)s - %(message)s')  # noqa: E501

    # Process Start Time
    start_time = time.time()
    logger.info("Starting Strut Process.")

    # Grab strut information and calculate Pace and Progress Summary
    strutActiveStudents = asyncio.run(strut.strut_active_students())
    strutEnrollments = asyncio.run(strut.strut_student_enrollments(strutActiveStudents))
    processedStudents = asyncio.run(strut.handle_progress_student_data(strutActiveStudents, strutEnrollments))

    # Update and Insert into Salesforce
    sfClient = asyncio.run(salesforce.login_salesforce())
    studentContactData = asyncio.run(salesforce.grab_student_contact_data(sfClient))
    studentsToUpdate = asyncio.run(salesforce.update_student_progress(processedStudents, studentContactData))
    if len(studentsToUpdate) > 0:
        asyncio.run(salesforce.update_salesforce_bulk_contact_data_by_contactID(sfClient, studentsToUpdate))

    logger.info("--- %s seconds ---" % (time.time() - start_time))


if __name__ == "__main__":
    main()
