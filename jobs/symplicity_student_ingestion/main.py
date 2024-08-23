import os
import sys
import traceback
from propus import Logging

from symplicity_ingestion import SymplicityIngestion


logger = Logging.get_logger("main.py")


def main():
    try:
        process = SymplicityIngestion.build(os.environ.get("ENV", "dev"))
        process.run()
        logger.info("Simplicity ingestion completed successfully")
    except Exception as err:
        logger.error("process failed exceution. Error: %s", str(err))
        traceback.print_exc(file=sys.stdout)


if __name__ == "__main__":
    main()
