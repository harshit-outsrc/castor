import os

from propus.calbright_sql.calbright import Calbright
from propus.anthology import Anthology


def setup_anthology(anthology_ssm, ssm):
    anthology_client = Anthology(**ssm.get_param(anthology_ssm, param_type="json"))
    anthology_client.timeout = 60
    return anthology_client


def setup_postgres_engine(psql_ssm, ssm):
    try:
        if psql_ssm == "localhost":
            calbright_postgres = Calbright.build(
                {
                    "db": os.environ.get("DB"),
                    "host": "localhost",
                    "user": os.environ.get("USER"),
                    "password": os.environ.get("PASSWORD"),
                },
                verbose=False,
            )
        else:
            psql_staging_creds = ssm.get_param(psql_ssm, param_type="json")
            calbright_postgres = Calbright.build(psql_staging_creds)
        return calbright_postgres
    except Exception as err:
        raise err
