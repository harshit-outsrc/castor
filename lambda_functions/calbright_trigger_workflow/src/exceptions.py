class UnknownPSQLTriggerType(Exception):
    """Exception raised for an unrecognized psql trigger sent

    Attributes:
        psql_trigger_type -- Name of the psql_trigger_type sent into the workflow system
    """

    def __init__(self, psql_trigger_type):
        super().__init__(f'PSQL Trigger type "{psql_trigger_type}" unrecognized')


class MissingRequiredField(Exception):
    """Exception raised for missing required fields

    Attributes:
        psql_trigger_type -- Name of the psql_trigger_type sent into the workflow system
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


class UnrecognizedGrade(Exception):
    """Exception raised for an unrecognized grade existing

    Attributes:
        grade_value -- Value of the grade variable that could not be determined
    """

    def __init__(self, grade_value):
        super().__init__(f'Grade value "{grade_value}" unrecognized')


class MissingRecordInformation(Exception):
    """Exception raised for missing record information

    Attributes:
        record -- Record that is missing information
    """

    def __init__(self, record):
        super().__init__(f'Record "{record}" missing information for workflow')


class MissingAnthologyInformation(Exception):
    """Exception raised for missing anthology information

    Attributes:
        record -- Record that is missing anthology information
    """

    def __init__(self, record):
        super().__init__(f'Record "{record}" missing required anthology information for workflow')


class UnrecognizedAnthologyData(Exception):
    """Exception raised for response data from anthology that doesn't match what is expected

    Attributes:
        anthology_id -- Anthology id used for fetching data
        type -- type of structure expected from api request
    """

    def __init__(self, anthology_id, type):
        super().__init__(f"Anthology ID: {anthology_id} returned unexpected results for type: {type}")


class FailedAnthologyRegistration(Exception):
    """Exception raised for failed anthology registration

    Attributes:
        record -- Record that failed anthology registration
    """

    def __init__(self, record):
        super().__init__(f"Anthology Course unable to register for record: {record}")
