from configuration.constants import (
    SSM_ANTHOLOGY_PROD,
    SSM_PSQL_PROD,
    SSM_DLQ_PROD,
)

prod_configs = {
    # ssm
    "anthology_ssm": SSM_ANTHOLOGY_PROD,
    "psql_ssm": SSM_PSQL_PROD,
    "dlq_ssm": SSM_DLQ_PROD,
}
