import asyncio
from datetime import datetime, timedelta
import os

from propus.anthology import Anthology
from propus.aws.ssm import AWS_SSM
from propus.calbright_sql.calbright import Calbright
from propus import Logging
from propus.salesforce import Salesforce

from propus.calbright_sql.term import Term
from propus.helpers.anthology import create_term
from propus.helpers.calbright import format_term_name


class MissingAnthologyTerm(Exception):
    pass


class TermCreation:
    def __init__(self, sforce, calbright, anthology):
        self.sforce = sforce
        self.calbright = calbright
        self.anthology = anthology

        self.logger = Logging.get_logger("term_creation.py")
        sd = datetime.now()
        self.start_date = datetime(sd.year, sd.month, sd.day)
        # End date is 8 weeks from today
        self.end_date = datetime.now() + timedelta(days=8 * 7)

    @staticmethod
    def build(env):
        ssm = AWS_SSM.build()
        db_configs = {
            "db": os.environ.get("DB"),
            "host": "localhost",
            "user": os.environ.get("USER"),
            "password": os.environ.get("PASSWORD"),
        }

        anthology_creds = ssm.get_param(f"anthology.{env if env == 'prod' else 'test'}", "json")
        db_configs = ssm.get_param(f"psql.calbright.{env if env == 'prod' else 'stage'}.write", "json")

        return TermCreation(
            sforce=Salesforce.build_v2(env if env == "prod" else "stage", ssm),
            calbright=Calbright.build(db_configs),
            anthology=Anthology(**anthology_creds),
        )

    def fetch_anthology_terms(self):
        """Fetch academic terms from the anthology API.

        This function retrieves academic term configurations from the anthology
        API and filters them based on start date.

        It runs the anthology's fetch_configurations method to get all terms.
        It then iterates through each term, parsing the start date and comparing
        it to the self.start_date cutoff.

        Matching terms have their ID stored in a dictionary keyed by the start date.

        Returns:
            dict: A dictionary of term IDs indexed by start date
        """
        academic_terms = asyncio.run(self.anthology.fetch_configurations("term"))
        start_dates = {}
        for term in academic_terms.get("value"):
            start_date = self.start_date.strptime(term.get("StartDate").split("T")[0], "%Y-%m-%d")
            if start_date < self.start_date:
                continue
            start_dates[term.get("StartDate").split("T")[0]] = term.get("Id")
        return start_dates

    def run(self):
        """Create academic terms across systems.

        This function synchronizes academic term data between different systems
        by creating terms that are missing in each system.

        It first fetches existing term data from Anthology and Salesforce APIs.
        It then queries the Calbright database for existing terms.

        For each week between the start and end dates, it checks if a term exists
        in each system. If not, it creates the term in the respective system.

        Any missing required terms in Anthology will cause an exception.

        Once complete, it commits any changes to the Calbright database.
        """
        future_anthology_terms = self.fetch_anthology_terms()
        future_sf_terms_by_start_date = {t.get("hed__Start_Date__c"): t for t in self.sforce.fetch_terms(False)}
        future_calbright_db_terms = [
            r[0].strftime("%Y-%m-%d")
            for r in (
                self.calbright.session.query(Term.start_date)
                .filter(Term.start_date >= self.start_date)
                .order_by(Term.start_date)
                .all()
            )
        ]

        days_ahead = 1 - self.start_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        start_date = self.start_date + timedelta(days_ahead)
        while start_date < self.end_date:
            fmt_start_date = start_date.strftime("%Y-%m-%d")
            term_name = format_term_name(start_date)
            if fmt_start_date not in future_sf_terms_by_start_date:
                # Missing Term In Salesforce
                self.sforce.create_term(start_date)
                self.logger.info(f"Created Term in Salesforce for {fmt_start_date}")
            if fmt_start_date not in future_anthology_terms:
                # Missing Term In Anthology
                term_id = create_term(self.anthology, start_date, term_name)
                future_anthology_terms[fmt_start_date] = term_id
                self.logger.info(f"Created Term in Anthology for {fmt_start_date}")
            if fmt_start_date not in future_calbright_db_terms:
                # Missing Term In Calbright Database
                if not future_anthology_terms.get(fmt_start_date):
                    raise MissingAnthologyTerm(f"Missing Required Anthology Term for {fmt_start_date}")
                self.calbright.session.add(
                    Term(
                        term_name=term_name,
                        start_date=fmt_start_date,
                        end_date=start_date + timedelta(days=181),
                        add_drop_date=start_date + timedelta(days=30),
                        anthology_id=future_anthology_terms.get(fmt_start_date),
                    )
                )
                self.logger.info(f"Created Term in Calbright database for {fmt_start_date}")

            start_date += timedelta(days=7)
        self.calbright.session.commit()
