import re

from propus.aws.ssm import AWS_SSM
from propus.helpers.salesforce import (
    SF_EXPRESS_INTEREST_MAP,
    SF_SOURCE_MAP,
    SF_FK_EXPRESS_INTEREST_MAP,
    SF_FK_EXPRESS_INTEREST_INTERMEDIARY_MAP,
    SF_FK_EXPRESS_INTEREST_MULTI_MAP,
    SF_INDEX_MAP,
    get_or_create_source,
    create_express_interest_per_program_of_interest,
)
from propus.helpers.etl import clean_phone
from propus.helpers.sql_alchemy import build_query
from propus.salesforce.salesforce import Salesforce
from propus.sql.calbright.expressed_interest import ExpressInterest


# Data is being collected from the SalesForce Contact table
table = "Contact"
# Contact fields that are being queried
fields = (
    [k for k, v in SF_INDEX_MAP.items()]
    + [k for k, v in SF_EXPRESS_INTEREST_MAP.items()]
    + [k for k, v in SF_SOURCE_MAP.items()]
    + [k for k, v in SF_FK_EXPRESS_INTEREST_MAP.items()]
    + [k for k, v in SF_FK_EXPRESS_INTEREST_INTERMEDIARY_MAP.items()]
    + [k for k, v in SF_FK_EXPRESS_INTEREST_MULTI_MAP.items()]
)

# Basic filters to remove test data and look for students with CCC IDs only
filters = [
    "Test_Demo__c = false",
    "cfg_Programs_of_Interest__c not in ('')",
]


def ingest_expressed_interest(session):
    """Ingest Express Interest records from SalesForce.
    Arguments:
        session: SQL Alchemy database session
    """

    ssm = AWS_SSM.build()
    sf = Salesforce.build(**ssm.get_param(parameter_name="salesforce.propus.stage", param_type="json"))
    qry = build_query(table=table, fields=fields, filters=filters)
    results = sf.bulk_custom_query_operation(qry, max_tries=4, dict_format=True)

    # Provide blanks instead of nulls for required Express Interest fields
    non_nullable_args = {
        "first_name": "",
        "last_name": "",
        "email": "",
        "phone_number": "",
    }

    print(f"Records found: {len(results)}")

    for record in results:
        # Populate the contact arguments from the SalesForce query
        contact_args = (
            non_nullable_args
            | {v: record.get(k) for k, v in SF_EXPRESS_INTEREST_MAP.items() if record.get(k)}
            | {v: record.get(k) for k, v in SF_INDEX_MAP.items() if record.get(k)}
        )

        contact_args["phone_number"] = (
            clean_phone(contact_args.get("phone_number")) if contact_args.get("phone_number") else ""
        )

        for sf_id_field, map_tuple in SF_FK_EXPRESS_INTEREST_MAP.items():
            if record.get(sf_id_field):
                map_fn, student_id_field = map_tuple
                field_map = map_fn(session)
                contact_args[student_id_field] = field_map[record[sf_id_field]]

        # Prints the missing fields, but will still add the record with missing required fields
        for k, v in non_nullable_args.items():
            if contact_args[k] == v:
                print(f"Contact {contact_args['salesforce_id']} is missing required {k} value")

        if len(record.get("cfg_CCC_ID__c")) == 7:
            contact_args["converted"] = True

        source = get_or_create_source(session, record, record.get("LeadSource"))
        contact_args["source_id"] = source.id

        programs_of_interest_list = (
            re.split(r"\s*[,;]\s*", record.get("cfg_Programs_of_Interest__c").strip())
            if record.get("cfg_Programs_of_Interest__c")
            else None
        )

        if programs_of_interest_list:
            create_express_interest_per_program_of_interest(session, contact_args, programs_of_interest_list)
        else:
            new_express_interest = ExpressInterest(**contact_args)
            session.add(new_express_interest)
            print(f"Contact {contact_args['salesforce_id']} missing program of interest while creating record")

    else:
        print("No records found")

    session.commit()
