class UnknownTriggerType(Exception):
    """Exception raised for an unrecognized psql trigger sent

    Attributes:
        trigger_payload -- Name of the trigger_payload sent into the psql trigger system
    """

    def __init__(self, trigger_payload):
        super().__init__(f'PSQL Trigger type for "{trigger_payload}" unrecognized')


class MissingRequiredField(Exception):
    """Exception raised for missing required fields

    Attributes:
        psql_trigger_type -- Name of the psql_trigger_type sent into the psql trigger system
        field -- field that is missing
    """

    def __init__(self, psql_trigger_type, field):
        super().__init__(
            f'PSQL Trigger type "{psql_trigger_type}" is missing or size is 0 for the required field: {field}'
        )


class DuplicatePSQLRecordsFound(Exception):
    """Exception raised for mulple records in PSQL matching data

    Attributes:
        trigger_data -- trigger data used to search for records
    """

    def __init__(self, trigger_data):
        super().__init__(f"Duplicate Records Found: {trigger_data} returns multiple records that exist in PSQL")
