#!/usr/bin/python3

import os
import student_integrations.student_account
from salesforce_api import Salesforce
from dotenv import load_dotenv
from propus import Logging

logger = Logging.get_logger("castor/jobs/vcg_sftp_student_uploader/student_integrations/salesforce")

# Set Async Loop policy to avoid RuntimeError
# asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()
SALESFORCE_URL = "https://calbright.my.salesforce.com"

# Salesforce API Request Variables
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
    # SALESFORCE_QUERY = """select Id, cfg_CCC_ID__c, FirstName, LastName, cfg_Calbright_Email__c,
    #                     cfg_Learner_Status__c, Learner_Status_Number__c from Contact where cfg_Learner_Status__c
    #                     in('Enrolled in Program Pathway', 'Started Program Pathway') and RecordType.Name
    #                      = 'Learner Contact' and cfg_CCC_ID__c like '%' and Id = '0035G00001m2W8oQAE'"""
    # production query
    SALESFORCE_QUERY = """select Id, cfg_CCC_ID__c, FirstName, LastName, cfg_Calbright_Email__c, cfg_Learner_Status__c,
                        Learner_Status_Number__c from Contact where cfg_Learner_Status__c in('Started Program Pathway')
                        and RecordType.Name = 'Learner Contact' and Test_Demo__c = false and cfg_CCC_ID__c like '%'"""

    logger.info("Querying student contact information.")
    studentData = client.sobjects.query(SALESFORCE_QUERY)
    # print("Salesforce Query Returned: ", studentData)
    return studentData


async def update_salesforce_bulk_contact_data_by_contactID(client, dataToUpdate):
    response = client.bulk.update("Contact", dataToUpdate)
    logger.info(response)
    return response


async def format_student_information(studentAccountData):
    # loop through salesforce queried data and format account information to meet VCG .csv requirements
    formattedStudentAccountData = []
    for studentAccount in studentAccountData:
        logger.info(f'Formatting Student ID: {studentAccount.get("Id")} - {studentAccount.get("cfg_CCC_ID__c")}')
        student = student_integrations.student_account.StudentVCGAccount()
        student.first_name = studentAccount.get("FirstName")
        student.last_name = studentAccount.get("LastName")
        student.email = studentAccount.get("cfg_Calbright_Email__c")
        student.member_id = studentAccount.get("cfg_CCC_ID__c")
        # student.date_of_birth # this is not used currently as we do not record this information, for sake of what can
        # be accepted it has been commented out
        formattedStudentAccountData.append(student)

    return formattedStudentAccountData
