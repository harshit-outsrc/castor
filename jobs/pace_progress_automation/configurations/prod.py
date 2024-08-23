from configurations.constant_config import GDRIVE_SSM, GSHEET_SSM, HUBSPOT_SSM, SALESFORCE_PROD_SSM

prod_configs = {
    "use_test_email": False,
    "pdf_url": "https://script.google.com/macros/s/AKfycbzBFksQaAN9-lc_0bR04cmo0mxnqme6_mrHvdOSQeYNW8LCWf-8nlz4LP-hBse8ZfHzbg/exec",  # noqa:E501
    "gsheet": {
        "url": "https://docs.google.com/spreadsheets/d/1ZqT8YAgPL4T_ahLh6I5WP4guJ8l_G68hNH1Vkv2siU8/edit#gid=1024855191",  # noqa:E501
        "tabs": [2, 3],
        "expected_tab_names": ["G3 Automation", "G1/4 Automation"],
    },
    "ssm": {"gdrive": GDRIVE_SSM, "gsheet": GSHEET_SSM, "hubspot": HUBSPOT_SSM, "salesforce": SALESFORCE_PROD_SSM},
    "email_templates": {
        "90 Day": {"welcome_email": 128182754361, "update_email": 128402865302},
        "120 Day": {"welcome_email": 128195457603, "update_email": 128942985141},
        "180 Day": {"welcome_email": 128208928294, "update_email": 128942463041},
        "365 Day": {"welcome_email": 128209408849, "update_email": 128934251274},
        "stopout": 130078312563,
    },
}
