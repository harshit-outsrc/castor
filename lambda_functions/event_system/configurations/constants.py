# SSMs
SSM_CONSTANTS_DEV = "constants.dev"
SSM_CONSTANTS_PROD = "constants.prod"
SSM_CONSTANTS_STAGE = "constants.stage"

SSM_CALBRIGHT_PROD_WRITE = "psql.calbright.prod.write"
SSM_CALBRIGHT_STAGE_WRITE = "psql.calbright.stage.write"
SSM_CALBRIGHT_DEV_WRITE = "psql.calbright.dev.write"

SSM_CANVAS_STAGE = "canvas.stage.token"
SSM_CANVAS = "canvas.prod.token"

SSM_FEATURE_FLAGS_DEV = "feature_flags.dev"
SSM_FEATURE_FLAGS_PROD = "feature_flags.prod"
SSM_FEATURE_FLAGS_STAGE = "feature_flags.stage"

SSM_SALESFORCE_STAGE = "salesforce.propus.stage"
SSM_SALESFORCE_PROD = "salesforce.propus.prod"

SSM_GDRIVE = "gsuite.svc-engineering"
SSM_GSHEETS_STUDENTS = "gsuite.calbright-student.users"
SSM_GSHEETS_SVC_ENGINEERING = "gsuite.svc-engineering.sheets"
SSM_GSUITE_SVC_ENGINEERING_LICENSING = "gsuite.svc-engineering.licensing"

SSM_GEOLOCATOR_STAGE = "google_maps.propus.stage"

SSM_SLACK = "slack.calbright-college.prod"

SSM_STRUT = "lms.strut"
SSM_STRUT_SANDBOX = "lms.strut.sandbox"
SSM_STRUT_PROD = "lms.strut.prod"

SSM_HUBSPOT = "hubspot.production"

SSM_CALENDLY = "calendly.production"

SSM_IRONIKUS_BETA = "ironikus.beta"
SSM_IRONIKUS_PROD = "ironikus.prod"

PANDADOC_SANDBOX = "pandadoc.sandbox"
PANDADOC_PROD = "pandadoc.production"

# Hubspot Email Templates
STAGE_VS_INTAKE_EMAIL = 114879015798
PROD_VS_INTAKE_EMAIL = 115635608160
CSEP_COMPLETE_EMAIL_ID = 145977075626
CSEP_DEVICE_REQUEST_EMAIL_ID = 168761880141

# Google Drive Folder IDs
STAGE_GDRIVE_VS_PARENT_FOLDER = "1iy6jggaVy71epoDXoYIvMZM9iO7qKgue"
PROD_GDRIVE_VS_PARENT_FOLDER = "1OLXqUpd3bZ8BFXfiwGaGWzu6GpLi4JSG"

# Gsheets Keys
PROD_SHEET_KEYS_MAP = {
    "adjust_ou_to_enrolled_student": "10k3-rXq3rh6N2cN-bZQRsagPWg_q1jBczHOuy9wEtS0",
    "enqueue_student_deprovision": "1rkz6z-b0L6AsnQ6Lov9UpHKh1eUunhmeeafuMTORVD8",
    "enqueue_student_to_strut": "1xpfowjTgUfKVPocpdhEvz5EMcooO7IHOZTgjAX0cBqI",
    "loaner_device_management": "1yzdGpTiS0MdDAU6W_yvb4JHBzAhnH7KS8y9x5vfFKZU",
    "tangoe_requests_tab": 6,
}

STAGE_SHEET_KEYS_MAP = {
    "adjust_ou_to_enrolled_student": "1mHr8l8A_y33M7A5QQPIn3JDy3tmipwoFHH71qwt5j4w",
    "enqueue_student_deprovision": "1zlRAj-e_eIQmwHFUk5qq1-HEGGQcZ8sXN5bKrT73RYM",
    "enqueue_student_to_strut": "1EClezfiz8kFxIhRs_aiUeFwlQ8cDScM19-OT3cfHO9M",
    "loaner_device_management": "1tKaXjxJeaRz1vnwwM6zMYhxD_r9Mb0P1v28eCdtNE8U",
    "tangoe_requests_tab": 13,
}

SSM_TANGOE_DEV = "tangoe.dev"
SSM_TANGOE_PROD = "tangoe.prod"
SSM_TANGOE_STAGE = "tangoe.stage"
