#!/usr/bin/python3

import os
import pandas
from salesforce_api import Salesforce
from dotenv import load_dotenv
from propus.logging_utility import Logging

logger = Logging.get_logger("castor/jobs/strut_progress_activity_tracker/student_integrations/salesforce")

load_dotenv()
SALESFORCE_URL = "https://calbright.my.salesforce.com"

# Castor API Request Variables
SALESFORCE_USERNAME = os.getenv("SALESFORCE_USERNAME")
SALESFORCE_PASSWORD = os.getenv("SALESFORCE_PASSWORD")
SALESFORCE_SEC_TOKEN = os.getenv("SALESFORCE_SECURITY_TOKEN")
SALESFORCE_CONSUMER_SECRET = os.getenv("SALESFORCE_CONSUMER_SECRET")
SALESFORCE_CONSUMER_KEY = os.getenv("SALESFORCE_CONSUMER_KEY")
SALESFORCE_API_VERSION = os.getenv("SALESFORCE_API_VERSION")


async def login_salesforce():
    logger.info("Authenticating Salesforce Login.")
    # Start Salesforce API Client Login
    client = Salesforce(username=SALESFORCE_USERNAME, password=SALESFORCE_PASSWORD, security_token=SALESFORCE_SEC_TOKEN)
    return client


async def grab_student_contact_data(client):
    # test query
    # SALESFORCE_QUERY = """select Id, cfg_CCC_ID__c, cfg_Strut_User_ID__c, cfg_Strut_Username__c, FirstName, LastName,
    #                     cfg_Calbright_Email__c, cfg_Learner_Status__c, Learner_Status_Number__c,
    #                     cfg_Intended_Program__c, Program_Version__c, Last_Strut_Activity_Timestamp__c, Course_1__c,
    #                     Course_1_Pace__c, Course_1_Progress__c, Completed_Course_1__c, Course_2__c, Course_2_Pace__c,
    #                     Course_2_Progress__c, Completed_Course_2__c, Course_3__c, Course_3_Pace__c,
    #                     Course_3_Progress__c, Completed_Course_3__c from Contact where cfg_Learner_Status__c
    #                     in('Enrolled in Program Pathway', 'Started Program Pathway', 'Completed Program Pathway') and
    #                     RecordType.Name = 'Learner Contact' and cfg_Intended_Program__c not in ('T2T CRM Admin', '')
    #                     and cfg_Strut_User_ID__c like '%' and cfg_Calbright_Email__c like 'jesse.lawson%'"""
    # production query
    SALESFORCE_QUERY = """select Id, cfg_CCC_ID__c, cfg_Strut_User_ID__c, cfg_Strut_Username__c, FirstName, LastName,
                        cfg_Calbright_Email__c, cfg_Learner_Status__c, Learner_Status_Number__c,
                        cfg_Intended_Program__c, Program_Version__c, Last_Strut_Activity_Timestamp__c, Course_1__c,
                        Course_1_Pace__c, Course_1_Progress__c, Completed_Course_1__c, Course_2__c, Course_2_Pace__c,
                        Course_2_Progress__c, Completed_Course_2__c, Course_3__c, Course_3_Pace__c,
                        Course_3_Progress__c, Completed_Course_3__c from Contact where cfg_Learner_Status__c
                        in('Enrolled in Program Pathway', 'Started Program Pathway', 'Completed Program Pathway') and
                        RecordType.Name = 'Learner Contact' and cfg_Intended_Program__c not in ('T2T CRM Admin', '')
                        and cfg_Strut_User_ID__c like '%' and LMS__c = 'Strut'"""

    logger.info("Querying student contact information.")
    studentData = client.sobjects.query(SALESFORCE_QUERY)
    # print("Salesforce Query Returned: ", studentData)
    return studentData


async def update_salesforce_bulk_contact_data_by_contactID(client, dataToUpdate):
    response = client.bulk.update("Contact", dataToUpdate)
    logger.info(response)
    return response


async def update_student_progress(strutList, salesforceList):
    logger.info("Update student contact with Progress data.")
    index = 0
    contactsToUpdate = []

    # loop through strut processed list and update according to salesforce query returned where processed students exist
    for strutStudent in strutList:
        logger.info(f"Looking for Student: {strutStudent.strut_id} - {strutStudent.strut_username}")
        for sfStudent in salesforceList:
            if sfStudent["cfg_Strut_User_ID__c"] == str(strutStudent.strut_id):
                courseCount = len(strutStudent.student_summary)

                # Format Program Version for updating and tracking on Student Contact record
                program_version = (
                    lambda: "",
                    lambda: str(strutStudent.versions[0]["course_name"])
                    + " - v"
                    + str(strutStudent.versions[0]["version"]),
                )[len(strutStudent.versions) >= 1]()
                program_version += (
                    lambda: "",
                    lambda: ", "
                    + str(strutStudent.versions[1]["course_name"])
                    + " - v"
                    + str(strutStudent.versions[1]["version"]),
                )[len(strutStudent.versions) > 1]()
                program_version += (
                    lambda: "",
                    lambda: ", "
                    + str(strutStudent.versions[2]["course_name"])
                    + " - v"
                    + str(strutStudent.versions[2]["version"]),
                )[len(strutStudent.versions) > 2]()

                # INFO: PACE AND PROGRESS are swapped currently until a clear definition is determined
                # Verifies how many courses exist in the update of processed student for updating
                course1 = (lambda: "", lambda: strutStudent.student_summary[0].course)[courseCount >= 1]()
                # course1Pace = ''
                course1Progress = (lambda: "", lambda: strutStudent.student_summary[0].progress)[courseCount >= 1]()
                course1Completed = (lambda: "", lambda: strutStudent.student_summary[0].course_completed)[
                    courseCount >= 1
                ]()
                course2 = (lambda: "", lambda: strutStudent.student_summary[1].course)[courseCount > 1]()
                # course2Pace = ''
                course2Progress = (lambda: "", lambda: strutStudent.student_summary[1].progress)[courseCount > 1]()
                course2Completed = (lambda: "", lambda: strutStudent.student_summary[1].course_completed)[
                    courseCount > 1
                ]()
                course3 = (lambda: "", lambda: strutStudent.student_summary[2].course)[courseCount > 2]()
                # course3Pace = ''
                course3Progress = (lambda: "", lambda: strutStudent.student_summary[2].progress)[courseCount > 2]()
                course3Completed = (lambda: "", lambda: strutStudent.student_summary[2].course_completed)[
                    courseCount > 2
                ]()

                # Grab times and format for comparison to validate if there is a difference.
                last_strut_activity = pandas.to_datetime(strutStudent.last_activity_date)
                last_sf_activity = pandas.to_datetime(sfStudent["Last_Strut_Activity_Timestamp__c"])
                diff_time = (lambda: False, lambda: True)[last_sf_activity != last_strut_activity]()
                logger.info(
                    f"""Timestamp Compare: {diff_time}, {last_sf_activity}, {last_strut_activity},
                    Strut: {strutStudent.last_activity_date},"
                    Salesforce: {sfStudent.get("Last_Strut_Activity_Timestamp__c")}"""
                )

                # Removed CoursePace Updates since nothing to update
                # or (str(course1Pace) != str(sfStudent['Course_1_Pace__c'])) or (str(course2Pace) !=
                # str(sfStudent['Course_2_Pace__c']))
                if (
                    (str(program_version) != str(sfStudent["Program_Version__c"]))
                    or (diff_time)
                    or (str(course1) != str(sfStudent["Course_1__c"]))
                    or (str(course1Progress) != str(sfStudent["Course_1_Progress__c"]))
                    or (str(course1Completed) != str(sfStudent["Completed_Course_1__c"]))
                    or (str(course2) != str(sfStudent["Course_2__c"]))
                    or (str(course2Progress) != str(sfStudent["Course_2_Progress__c"]))
                    or (str(course2Completed) != str(sfStudent["Completed_Course_2__c"]))
                    or (str(course3) != str(sfStudent["Course_3__c"]))
                    or (str(course3Progress) != str(sfStudent["Course_3_Progress__c"]))
                    or (str(course3Completed) != str(sfStudent["Completed_Course_3__c"]))
                ):
                    # append the contact for update
                    contactsToUpdate.append(
                        {
                            "Id": sfStudent["Id"],
                            "Program_Version__c": program_version,
                            "Course_1__c": course1,
                            # 'Course_1_Pace__c': course1Pace,
                            "Course_1_Progress__c": course1Progress,
                            "Completed_Course_1__c": course1Completed,
                            "Course_2__c": course2,
                            # 'Course_2_Pace__c': course2Pace,
                            "Course_2_Progress__c": course2Progress,
                            "Completed_Course_2__c": course2Completed,
                            "Course_3__c": course3,
                            # 'Course_3_Pace__c': course3Pace,
                            "Course_3_Progress__c": course3Progress,
                            "Completed_Course_3__c": course3Completed,
                            "Last_Strut_Activity_Timestamp__c": strutStudent.last_activity_date,
                        }
                    )
                    index += 1
                else:
                    logger.info("Already up to date, skipping.")

                # index += 1
                if len(contactsToUpdate) > 0:
                    logger.info(
                        f"""Processed for Updating {index} of {len(strutList)}
                        student contact records with Progress data. 1: {contactsToUpdate[-1]}"""
                    )
                else:
                    logger.info("No Contacts required updating.")

    return contactsToUpdate
