from . import read_s3_csv

from propus.calbright_sql.program import Program
from propus.calbright_sql.course import Course
from propus.helpers.sql_alchemy import update_or_create


def coci_program_upload(s3, key, stage_session, prod_session):
    """
    This function reads a CSV file from S3 containing program data and uploads it to the
    stage and production databases. For each row in the CSV file, it creates a dictionary
    with the program data and calls the `update_or_create` function to insert or update
    the program record in both the stage and production databases using the `Program` model.
    After processing all rows, it commits the changes to both databases.

    Args:
        s3 (AWS S3 Instance): An instance of the S3 service client.
        key (str): The S3 key (path) of the CSV file containing the program data.
        stage_session (Session): A SQLAlchemy session object for the stage database.
        prod_session (Session): A SQLAlchemy session object for the production database.
    """
    data = read_s3_csv(s3.s3_client, key)
    for row in data:
        program_data = {
            "program_name": row.get("TITLE"),
            "control_number": row.get("CONTROL NUMBER"),
            "top_code": row.get("TOP CODE"),
            "cip_code": row.get("CIP CODE"),
            "approved_date": row.get("APPROVED DATE"),
        }
        update_or_create(stage_session, Program, program_data, control_number=program_data.get("control_number"))
        update_or_create(prod_session, Program, program_data, control_number=program_data.get("control_number"))
    stage_session.commit()
    prod_session.commit()
    print("COCI Programs Upserted Successfully")


def coci_course_upload(s3, key, stage_session, prod_session):
    """
    This function reads a CSV file from S3 containing course data and uploads it to the
    stage and production databases. For each row in the CSV file, it creates a dictionary
    with the course data and calls the `update_or_create` function to insert or update
    the course record in both the stage and production databases using the `Program` model.
    After processing all rows, it commits the changes to both databases.

    Args:
        s3 (AWS S3 Instance): An instance of the S3 service client.
        key (str): The S3 key (path) of the CSV file containing the course data.
        stage_session (Session): A SQLAlchemy session object for the stage database.
        prod_session (Session): A SQLAlchemy session object for the production database.
    """
    data = read_s3_csv(s3.s3_client, key)
    for row in data:
        course_data = {
            "course_name": row.get("TITLE (CB02)"),
            "status": row.get("STATUS"),
            "course_id": row.get("COURSE ID"),
            "control_number": row.get("CONTROL NUMBER (CB00)"),
            "department_name": row.get("DEPARTMENT NAME (CB01A)"),
            "department_number": row.get("DEPARTMENT NUMBER (CB01B)"),
            "course_code": row.get("DEPARTMENT NAME (CB01A)") + row.get("DEPARTMENT NUMBER (CB01B)"),
            "course_classification_status": row.get("COURSE CLASSIFICATION STATUS (CB11)"),
            "top_code": row.get("TOP CODE (CB03)"),
            "last_updated_by_college": row.get("LAST UPDATED BY COLLEGE"),
            "minimum_course_contact_hours": row.get("MINIMUM COURSE CONTACT HOURS"),
            "maximum_course_contact_hours": row.get("MAXIMUM COURSE CONTACT HOURS"),
        }
        update_or_create(stage_session, Course, course_data, course_id=course_data.get("course_id"))
        update_or_create(prod_session, Course, course_data, course_id=course_data.get("course_id"))
    stage_session.commit()
    prod_session.commit()
    print("COCI Courses Upserted Successfully")
