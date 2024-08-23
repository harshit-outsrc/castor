class UnknownEventType(Exception):
    """Exception raised for an unrecognized event_type sent

    Attributes:
        event_type -- Name of the event_type sent into the event system
    """

    def __init__(self, event_type):
        super().__init__(f"Event type '{event_type}' is unrecognized")


class EmptyEventData(Exception):
    """Exception raised for an event sent with no data

    Attributes:
        event_type -- Name of the event_type sent into the event system
    """

    def __init__(self, event_type):
        super().__init__(f'Event type "{event_type}" was sent with no data')


class UnhandledEventData(Exception):
    """Exception raised for an error handling / parsing event data

    Attributes:
        event_type -- Name of the event_type sent into the event system
    """

    def __init__(self, event_type):
        super().__init__(f'Event type "{event_type}" error with data handling or parsing')


class MissingRequiredField(Exception):
    """Exception raised for missing required fields

    Attributes:
        event_type -- Name of the event_type sent into the event system
        field -- field that is missing
    """

    def __init__(self, event_type, field):
        super().__init__(f'Event type "{event_type}" is missing or size is 0 for the required field: {field}')


class CalbrightEmailNotInDatabase(Exception):
    """Exception raised for missing Calbright Email in Database

    Attributes:
        email -- email that was searched in Database
    """

    def __init__(self, email):
        super().__init__(f"Calbright Email {email} was not found in database")


class CccIdNotInDatabase(Exception):
    """Exception raised for missing CCC ID in Database

    Attributes:
        ccc_id -- ccc_id that was searched in Database
    """

    def __init__(self, ccc_id):
        super().__init__(f"CCC ID {ccc_id} was not found in database")


class CccIdNotInSalesforce(Exception):
    """Exception raised for missing CCC ID in Salesforce

    Attributes:
        ccc_id -- ccc_id that was searched in Salesforce
    """

    def __init__(self, ccc_id):
        super().__init__(f"CCC ID {ccc_id} was not found")


class MultipleCccIdInSalesforce(Exception):
    """Exception raised for multiple records in Salesforce with the same CCC ID

    Attributes:
        ccc_id -- ccc_id that was searched in Salesforce
    """

    def __init__(self, ccc_id):
        super().__init__(f"CCC ID {ccc_id} returns multiple records in Salesforce")


class CalbrightEmailNotInSalesforce(Exception):
    """Exception raised for missing Calbright Email in Salesforce

    Attributes:
        calbright_email -- calbright email address
    """

    def __init__(self, calbright_email):
        super().__init__(f"Calbright Email: {calbright_email} was not found")


class EmailNotInSalesforce(Exception):
    """Exception raised for missing Email in Salesforce

    Attributes:
        email -- calbright email address
    """

    def __init__(self, email):
        super().__init__(f"Email: {email} was not found (personal or calbright)")


class MultipleCalbrightEmailInSalesforce(Exception):
    """Exception raised for multiple records in Salesforce with the same Calbright Email

    Attributes:
        calbright_email -- calbright email address
    """

    def __init__(self, calbright_email):
        super().__init__(f"Calbright Email: {calbright_email} returns multiple records in Salesforce")


class NoVeteranRecordExists(Exception):
    """Exception raised when there is no veteran record when there was one expected

    Attributes:
        calbright_email -- calbright email address
    """

    def __init__(self, calbright_email):
        super().__init__(f"Calbright Email: {calbright_email} does not have an expected Veterans Record")


class UnknownCalendlyEventType(Exception):
    """Exception raised for an unrecognized calendly event sent

    Attributes:
        event_type -- Name of the event_type sent into the event system
    """

    def __init__(self, event_type):
        super().__init__(f'Calendly Event type "{event_type}" unrecognized')


class UnknownDocumentDownloadEventType(Exception):
    """Exception raised for an unrecognized document download event sent

    Attributes:
        event_type -- Name of the event_type sent into the event system
    """

    def __init__(self, event_type):
        super().__init__(f'Document Download Event type "{event_type}" unrecognized')


class InvalidLearnerStatus(Exception):
    """
    Exception raised for an invalid learner status
    """


class TangoePersonCreationError(Exception):
    """Error raised for an failure to create Tangoe Person

    Attributes:
        ccc_id -- Student CCC ID that failed tangoe person creation
    """

    def __init__(self, ccc_id):
        super().__init__(f'Could not create Tangoe person for  "{ccc_id}" ')


class TangoeActivityCreationError(Exception):
    """Error raised for an failure to create Tangoe Activity

    Attributes:
        ccc_id -- Student CCC ID that failed tangoe activity creation
    """

    def __init__(self, ccc_id):
        super().__init__(f'Could not create Tangoe activity for  "{ccc_id}" ')


class TangoeActivityReturnError(Exception):
    """Error raised for an failure to create Tangoe Activity

    Attributes:
        ccc_id -- Student CCC ID that failed tangoe activity return
    """

    def _init_(self, ccc_id):
        super()._init_(f'Could not return Tangoe activity for  "{ccc_id}" ')
class PandaDocCreationError(Exception):
    """Error raised for an failure to create/send PandaDoc

    Attributes:
        ccc_id -- Student CCC ID that failed PandaDoc process
    """

    def __init__(self, ccc_id, err):
        super().__init__(f"Could not create and send PandaDoc for Student {ccc_id}: {err}")
