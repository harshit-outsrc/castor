from datetime import datetime

INTENDED_PROGRAM_SLACK_TABLE = {
    "HC DEI": "log-dei-automations",
    "Cybersecurity": "enrollment-agreement",
    "IT Support": "enrollment-agreement",
    "Medical Coding": "enrollment-agreement",
    "Career Readiness": "log-career-readiness-automations",
    "T2T CRM Admin": "log-crmadmin-automations",
    "Data Analysis": "log-data-analysis-automations",
    "T2T Intro to Networks": "enrollment-agreement",
    "Project Management": "enrollment-agreement",
    "DEV_SLACK": "automations-test",
}

PROGRAM_API_VALUE_MAP = {
    "Upskilling for Equitable Health Impacts: Diversity, Equity, and Inclusion": "HC DEI",
    "Cybersecurity": "Cybersecurity",
    "IT Support": "IT Support",
    "Medical Coding": "Medical Coding",
    "Career Readiness": "Career Readiness",
    "Transition to Technology: CRM Platform Administration": "T2T CRM Admin",
    "Introduction to Data Analysis": "Data Analysis",
    "Transition to Technology: Introduction to Networks": "T2T Intro to Networks",
    "Project Management": "Project Management",
}

STRUT_COMPETENCY_IDS = {
    "Project Management": [
        268,
        269,
        270,
        271,
        272,
        273,
        274,
        275,
        276,
        277,
        278,
        279,
        280,
        281,
        282,
        283,
        284,
        285,
        286,
    ],
    "T2T Intro to Networks": [
        233,
        234,
        235,
        236,
        237,
        238,
        239,
        240,
        241,
        242,
        243,
        245,
        244,
        246,
        247,
        248,
        249,
        250,
        251,
        252,
        253,
    ],
    "Data Analysis": [222, 223, 224, 225, 226, 227, 228, 221, 229, 230, 231, 232],
    "Career Readiness": [153],
    "HC DEI": [152, 150],
    "Cybersecurity": [211],
    "IT Support": [214],
    "Medical Coding": [117, 37, 38, 39],
}

EXISTING_COMPETENCY_IDS_CHECK = {
    "Data Analysis": [207],
}

PROGRAM_PRODUCT_IDS = {
    "Project Management": [7],
    "T2T Intro to Networks": [5],
    "Data Analysis": [3],
}

EXISTING_COMPLETION_PRODUCT_IDS = {"Data Analysis": [4]}

COURSE_CODES_TABLE = {
    "a1m5G000005ss4DQAQ": "IT520 - v1.0",
    "a1m5G000006orWJQAY": "IT525 - v1.0",
    "a1m5G000008uTo5QAE": "IT520 - v3.0",
    "a1m5G000008uTo6QAE": "IT525 - v2.0",
}

VALID_LEARNER_STATUS = {
    "myTrailhead": ["Started Orientation", "Completed Orientation"],
    "Strut": ["Completed CSEP"],
    "Canvas": ["Completed CSEP"],
}


TANGOE_IDS = {
    "group_id": 6847,
    "new_base_country_membership_country_id": 52123291,
    "chromebook_activity_type_id": 22,
    "hotspot_activity_type_id": 45,
    "chromebook_business_ref_device_id": 246209,
    "hotspot_business_ref_device_id": 244156,
    "country_id": 52123291,
}

CANVAS_LAUNCH_DATES_BY_PROGRAM = {"Data Analysis": datetime(2024, 7, 24)}

PANDADOC_TEMPLATES = {"post_csep_dpau": "nAWxWqcFcvygsPMnpCVw4o", "enrollment_csep": "AYPN8iV8PeVahkVf9hzRMN"}
