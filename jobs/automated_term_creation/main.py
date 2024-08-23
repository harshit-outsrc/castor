import os
import sys
import traceback
from propus import Logging

from term_creation import TermCreation


logger = Logging.get_logger("main.py")


def main():
    """
    Main function runs the term creation process. Definition of environments:
     - dev:
        - localhost calbright DB
        - Test Anthology
        - Sandbox Salesforce
     - stage:
        - stage calbright DB
        - Test Anthology
        - Sandbox Salesforce
     - prod:
        - prod calbright DB
        - Prod Anthology
        - Prod Salesforce
    """
    try:
        process = TermCreation.build(os.environ.get("ENV", "dev"))
        process.run()
    except Exception as err:
        logger.error("process failed exceution. Error: %s", str(err))
        traceback.print_exc(file=sys.stdout)


if __name__ == "__main__":
    main()
