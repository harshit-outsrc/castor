from datetime import datetime, timezone
from unittest.mock import MagicMock


def create_mock_sf_services():
    mock_sf_services = MagicMock()

    def get_contact_field_side_effect(*args, **kwargs):
        if kwargs.get("sf_field") == "Last_Strut_SAA_Timestamp__c":
            return datetime(2024, 3, 30, 0, 18, tzinfo=timezone.utc)
        return "Some Field Value"

    mock_sf_services.get_contact_field.side_effect = get_contact_field_side_effect

    mock_sf_services.get_contact_saa_timestamp.return_value = datetime(2024, 3, 30, 0, 18, tzinfo=timezone.utc)
    mock_sf_services.update_contact_saa_timestamp.return_value = True
    mock_sf_services.get_contact_id.return_value = "CONTACT123"
    mock_sf_services.convert_event_timestamp_to_sf_datetime.return_value = datetime(
        2024, 3, 30, 0, 18, tzinfo=timezone.utc
    )
    mock_sf_services.update_contact_saa_timestamp.return_value = True
    mock_sf_services.get_courses.return_value = [{"id": "COURSE123", "name": "Test Course"}]
    mock_sf_services.update_course_progress.return_value = True
    mock_sf_services.update_course_completed.return_value = True
    mock_sf_services.update_last_lms_timestamp.return_value = True

    return mock_sf_services
