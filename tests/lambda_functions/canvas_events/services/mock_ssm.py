from unittest.mock import MagicMock


def create_mock_ssm():
    mock_ssm = MagicMock()

    # Define mock return values for get_param method
    mock_ssm.get_param.side_effect = lambda name, param_type=None: {
        "psql.calbright.staging.write": {"db": "foo", "host": "bar", "user": "foo", "password": "bar"},
        "canvas.test.token": {
            "base_url": "foo",
            "token": "bar",
            "auth_providers": {"google": 106, "okta": 107},
        },
    }.get(name, {})

    return mock_ssm
