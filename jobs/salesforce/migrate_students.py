import csv

from propus.aws.ssm import AWS_SSM
from propus.helpers.salesforce import (
    SF_ADDRESS_FIELDS,
    SF_CLEAN_FIELD_FUNCTIONS,
    SF_CONTACT_FIELD_MAP,
    SF_FK_MAP,
    SF_FK_INTERMEDIARY_MAP,
    SF_INDEX_MAP,
    create_student_addresses,
    create_student_ethnicity,
)
from propus.helpers.sql_alchemy import build_query
from propus.salesforce.salesforce import Salesforce
from propus.sql.calbright.student import Student


# Data is being collected from the SalesForce Contact table
table = "Contact"
# Contact fields that are being queried
fields = (
    SF_ADDRESS_FIELDS
    + [k for k, v in SF_CONTACT_FIELD_MAP.items()]
    + [k for k, v in SF_FK_INTERMEDIARY_MAP.items()]
    + [k for k, v in SF_FK_MAP.items()]
    + [k for k, v in SF_INDEX_MAP.items()]
)

# Filter out specific learner statuses
exclude_learner_statuses = [
    "'Expressed Interest'",
    "'App Started'",
    "''",
]

# Basic filters to remove test data and look for students with CCC IDs only
filters = [
    "Test_Demo__c = false",
    "cfg_CCC_ID__c <> Null",
    f"cfg_Learner_Status__c not in ({', '.join(exclude_learner_statuses)})",
]


def build_extract_data(seed_data_file_object):
    print("Parsing student extract file...")
    extract_data = {}
    reader = csv.DictReader(seed_data_file_object)
    for row in reader:
        # Set variables from the main file
        ccc_id = row.get("StudentNumber")
        first_name = row.get("FirstName", "")
        last_name = row.get("LastName", "")
        phone = row.get("Phone")
        work_phone = row.get("WorkPhone")
        calbright_email = row.get("Email")
        personal_email = row.get("OtherEmail")
        ssn = row.get("SSN")
        address1 = row.get("Address1", "")
        address2 = row.get("Address2")
        city = row.get("City", "")
        state = row.get("State", "CA")
        zip = row.get("Zip", "")
        country = row.get("CountryCode", "USA")
        address = {
            "address1": address1,
            "address2": address2,
            "city": city,
            "state": state,
            "zip": zip,
            "country": country,
        }
        ethnicity = []
        for i in range(1, 6):
            e = row.get(f"RaceCode{i}")
            if e:
                ethnicity.append(e)
            else:
                break

        extract_data[ccc_id] = {
            "first_name": first_name,
            "last_name": last_name,
            "address": address,
            "ethnicity": ethnicity,
            "phone_number": phone,
            "other_number": work_phone,
            "calbright_email": calbright_email,
            "personal_email": personal_email,
            "ssn": ssn,
        }
    return extract_data


def migrate_students(session, seed_file=None, verbose=False):
    """Migrate Student records from SalesForce and from the StudentExtractData.

    Arguments:
        session: SQL Alchemy database session
        seed_file (optional): Pre-processed student extract data file.
        verbose (optional): Boolean (defaults to False) controlling
            the amount of information printed as the migration job runs.
    """
    # Parse the Student Extract data
    extract_data = build_extract_data(seed_file) if seed_file else {}

    ssm = AWS_SSM.build()
    sf = Salesforce.build(**ssm.get_param(parameter_name="salesforce.propus.stage", param_type="json"))
    qry = build_query(table=table, fields=fields, filters=filters)
    results = sf.custom_query(qry)

    # Provide blanks instead of nulls for required Student fields
    non_nullable_args = {
        "first_name": "",
        "last_name": "",
        "personal_email": "",
    }

    if results.get("totalSize") > 0:
        print(f"Records found: {results.get('totalSize')}")
        # We are not processing any sf records that do not have a ccc_id
        ccc_id_records = [r for r in results.get("records") if r.get("cfg_CCC_ID__c")]
        print(f"Records to be processed: {len(ccc_id_records)}...")
        counter = 0
        for sf_student in ccc_id_records:
            counter += 1
            if counter % 100 == 0:
                print(f"    Processing record {counter}")
            current_ccc_id = sf_student["cfg_CCC_ID__c"]
            if len(current_ccc_id) != 7:
                print(f"Skipping student. CCC ID is not seven characters: {current_ccc_id}:")
                continue
            if verbose:
                print(f"Processing student {current_ccc_id}:")
            # Get details from student extract
            student_extract = extract_data.get(current_ccc_id, {})
            extract_address = student_extract.pop("address") if student_extract.get("address") else {}
            student_ethicity_list = student_extract.pop("ethnicity") if student_extract.get("ethnicity") else {}
            # Populate the student arguments from the student extract / SalesForce query
            student_args = (
                non_nullable_args
                | student_extract
                | {v: sf_student.get(k) for k, v in SF_CONTACT_FIELD_MAP.items() if sf_student.get(k)}
                | {v: sf_student.get(k) for k, v in SF_INDEX_MAP.items() if sf_student.get(k)}
            )

            # Clean values prior to storing in the database
            for k, v_fn in SF_CLEAN_FIELD_FUNCTIONS.items():
                if student_args.get(k):
                    try:
                        student_args[k] = v_fn(student_args[k])
                    except Exception as e:
                        print(f"Error cleaning {k} value {student_args.get(k)}: {e}")
                        student_args[k] = None

            # Add values from SalesForce that belong to a direct foreign key in Postgres
            # E.g., Student.pronoun_id = Pronoun.id
            for sf_id_field, map_tuple in SF_FK_MAP.items():
                if sf_student.get(sf_id_field):
                    map_fn, student_id_field = map_tuple
                    field_map = map_fn(session)
                    student_args[student_id_field] = field_map[sf_student[sf_id_field]]

            for k, v in non_nullable_args.items():
                if student_args[k] == v:
                    print(f"Student {student_args['ccc_id']} is missing required {k} value")
            new_student = Student(**student_args)
            session.add(new_student)
            if verbose:
                print(f"    Created new student {new_student}")

            # Process ethnicity from Student Extract
            if student_ethicity_list:
                create_student_ethnicity(session, new_student, student_ethicity_list)
                if verbose:
                    print(f"    Created student ethnicity records: {student_ethicity_list}")

            # Now that we have the new student record, create the other basic indirect relationships.
            # E.g., the StudentContactMethod object links Student and PreferredContactMethod,
            # and/or the models use ccc_id as joins instead of id fields.
            # The values from SalesForce are stored as strings / lists of strings.
            for sf_id_field, map_fn in SF_FK_INTERMEDIARY_MAP.items():
                if sf_student.get(sf_id_field):
                    sf_string = sf_student.get(sf_id_field)
                    map_fn(session, new_student, sf_string)

            # Process available student addresses
            addresses_dict = extract_address | {k: v for k, v in sf_student.items() if k in SF_ADDRESS_FIELDS}
            create_student_addresses(session, new_student, addresses_dict)

    else:
        print("No records found")

    session.commit()
