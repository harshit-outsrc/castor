from unittest.mock import MagicMock


def create_mock_canvas_services():
    mock_canvas_services = MagicMock()

    mock_canvas_services.create_next_course_enrollment.return_value = True

    mock_submission_history = [
        {"attempt": 1, "submitted_at": "2024-07-10T08:00:00", "score": 95},
        {"attempt": 2, "submitted_at": "2024-07-11T08:00:00", "score": 98},
    ]

    mock_assignment = {"submission_history": mock_submission_history}

    async def mock_get_single_submission(*args, **kwargs):
        return [mock_assignment]

    mock_canvas_services.canvas_engine.get_single_submission = MagicMock(side_effect=mock_get_single_submission)

    return mock_canvas_services
