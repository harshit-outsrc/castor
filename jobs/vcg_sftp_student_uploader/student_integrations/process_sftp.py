#!/usr/bin/python3

import os
import paramiko
import csv
import student_integrations.student_account
from datetime import datetime
from dotenv import load_dotenv
from propus import Logging

logger = Logging.get_logger("castor/jobs/vcg_sftp_student_uploader/student_integrations/process_sftp")

# Set Async Loop policy to avoid RuntimeError
# asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()
VCG_HOST = os.getenv("VCG_HOST")
VCG_USERNAME = os.getenv("VCG_USERNAME")


# Need to create csv with schoolname_yyyymmdd.csv, which is CalbrightCollege_{currentDate}.csv
async def create_CSV(studentAccountData: list[student_integrations.student_account.StudentVCGAccount]):
    logger.info("Creating CSV File with Student Data.")
    fileLocation = "./vcg_files/vcg_student_accounts/"
    fileTitle = f'CalbrightCollege_{datetime.today().strftime("%Y%m%d")}.csv'
    logger.info(f'Date formatted yyyymmdd: {datetime.today().strftime("%Y%m%d")}')

    with open(fileLocation + fileTitle, "w", newline="") as csvfile:
        studentWriter = csv.writer(csvfile, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL)
        studentWriter.writerow(["first_name", "last_name", "email", "member_id", "date_of_birth"])
        for studentData in studentAccountData:
            studentWriter.writerow(
                [studentData.first_name, studentData.last_name, studentData.email, studentData.member_id]
            )

    logger.info("Created CSV File " + fileTitle)
    return fileTitle


async def process_file_and_upload_to_VCG(fileTitle: str):
    logger.info("Start SFTP connection.")

    dataFileLocation = f"./vcg_files/vcg_student_accounts/{fileTitle}"
    pKeyFileLocation = "./vcg_files/CalbrightCollege.pem"
    hostKeyFileLocation = "./vcg_files/authorized_keys"

    pkey = paramiko.RSAKey.from_private_key_file(pKeyFileLocation)
    client = paramiko.SSHClient()
    policy = paramiko.RejectPolicy()

    client.set_missing_host_key_policy(policy)
    client.load_host_keys(hostKeyFileLocation)
    client.connect(VCG_HOST, username=VCG_USERNAME, pkey=pkey, port=22)

    sftp_client = client.open_sftp()

    if os.path.isfile(dataFileLocation):
        sftp_client.put(dataFileLocation, fileTitle)
    else:
        raise IOError("Could not find dataFileLocation %s !!" % dataFileLocation)

    sftp_client.close()

    client.close()

    logger.info("End SFTP connection.")
    return
