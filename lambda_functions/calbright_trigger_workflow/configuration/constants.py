# SSMs
SSM_ANTHOLOGY_DEV = "anthology.test"
SSM_ANTHOLOGY_PROD = "anthology.prod"
SSM_ANTHOLOGY_STAGE = "anthology.stage"

SSM_PSQL_DEV = "localhost"
SSM_PSQL_PROD = "psql.calbright.prod.write"
SSM_PSQL_STAGE = "psql.calbright.stage.write"

SSM_DLQ_DEV = "localhost"
SSM_DLQ_PROD = "calbright_triggers_prod_dlq.fifo"
SSM_DLQ_STAGE = "calbright_triggers_stage_dlq.fifo"

# MAPPING CONSTANTS
CITIZEN_STATUS_CCCAPPLY_TO_SIS = {
    "1": 1,  # US Citizen
    "2": 5,  # Permanent Resident
    "3": 6,  # Temporary Resident
    "4": 7,  # Refugee / Asylee
    "5": 8,  # Student Visa (F-1 or M-1)
    "6": 3,  # Other/Unknown
    "X": 9,  # Noncredit Application
}
