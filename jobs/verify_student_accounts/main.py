import sys
import traceback
from propus import Logging

from verify_students import VerifyStudents


logger = Logging.get_logger("main.py")


def main():
    try:
        process = VerifyStudents.build()
        process.run()
    except Exception as err:
        logger.error("process failed exceution. Error: %s", str(err))
        traceback.print_exc(file=sys.stdout)


if __name__ == "__main__":
    main()
