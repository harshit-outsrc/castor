from configuration.constants import (
    SSM_ANTHOLOGY_STAGE,
    SSM_PSQL_STAGE,
    SSM_DLQ_STAGE,
)

stage_configs = {
    # ssm
    "anthology_ssm": SSM_ANTHOLOGY_STAGE,
    "psql_ssm": SSM_PSQL_STAGE,
    "dlq_ssm": SSM_DLQ_STAGE,
}
