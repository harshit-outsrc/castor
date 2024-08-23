from configuration.constants import (
    SSM_ANTHOLOGY_DEV,
    SSM_PSQL_DEV,
    SSM_DLQ_DEV,
)

dev_configs = {
    # ssm
    "anthology_ssm": SSM_ANTHOLOGY_DEV,
    "psql_ssm": SSM_PSQL_DEV,
    "dlq_ssm": SSM_DLQ_DEV,
}
