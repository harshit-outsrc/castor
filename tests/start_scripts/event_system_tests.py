import os
import sys

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append("/".join(current_path.split("/")[:-2] + "lambda_functions/event_system".split("/")))
from tests.lambda_functions.event_system.event_system_test import TestEventSystem
from tests.lambda_functions.event_system.events.calendly_event_test import TestCalendlyEvents
from tests.lambda_functions.event_system.events.csep_complete_test import TestEventCsepComplete
from tests.lambda_functions.event_system.events.document_download_test import TestEventDocumentDownload
from tests.lambda_functions.event_system.events.hubspot_forms_submission_test import TestEventHubspotFormSubmission
from tests.lambda_functions.event_system.events.salesforce_test import TestEventSalesforce
from tests.lambda_functions.event_system.events.sp_term_certified_test import TestSpTermCertified
from tests.lambda_functions.event_system.events.veteran_intake_complete_test import (
    TestEventVeteranIntakeComplete,
)
from tests.lambda_functions.event_system.events.tangoe_event_test import TestEventTangoeEvent
from tests.lambda_functions.event_system.events.dpau_request_test import TestEventDPAURequest
from tests.lambda_functions.event_system.events.dpau_complete_test import TestEventDPAUComplete

from tests.start_scripts.base import BaseTestClass


class EventSystem(BaseTestClass):
    def __init__(self, test_name):
        super().__init__(test_name)

        self.tests = [
            TestEventSystem,
            TestCalendlyEvents,
            TestEventCsepComplete,
            TestEventSalesforce,
            TestEventVeteranIntakeComplete,
            TestEventDocumentDownload,
            TestEventHubspotFormSubmission,
            TestEventTangoeEvent,
            TestEventDPAURequest,
            TestEventDPAUComplete,
            TestSpTermCertified,
        ]


if __name__ == "__main__":
    EventSystem("event_system").run()
