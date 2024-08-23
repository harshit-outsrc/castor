import os
import sys
import traceback
from configurations.dev import dev_configs
from configurations.prod import prod_configs
from pace_pipeline import PacePipeline

from propus import Logging


logger = Logging.get_logger("main.py")


def main():
    try:
        configs = dev_configs
        if os.environ.get("ENV", "test") == "prod":
            logger.info("Loading Production configurations")
            configs = prod_configs
        pp = PacePipeline.build(configs)
        pp.run_pipeline()
        logger.info("Process Completed Successfully")
    except Exception as err:
        logger.error(f"process failed exceution. Error: {err}")
        traceback.print_exc(file=sys.stdout)


if __name__ == "__main__":
    main()
