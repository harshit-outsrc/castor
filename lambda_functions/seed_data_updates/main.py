try:
    import unzip_requirements  # noqa
except ImportError:
    pass

from tasks.coci_file_upload import coci_program_upload, coci_course_upload
from tasks.staff_data_upload import staff_data_upload

from propus.aws.s3 import AWS_S3
from propus.aws.ssm import AWS_SSM
from propus.calbright_sql.calbright import Calbright

KEY_MAP = {
    "seed_data/COCI-Program-Export.csv": coci_program_upload,
    "seed_data/COCI-Course-Export.csv": coci_course_upload,
    "seed_data/staff_data.csv": staff_data_upload,
}


def run(event, _):
    s3 = AWS_S3.build()
    ssm = AWS_SSM.build()
    stage_calbright = Calbright.build(ssm.get_param("psql.calbright.stage.write", "json"), verbose=False)
    prod_calbright = Calbright.build(ssm.get_param("psql.calbright.prod.write", "json"), verbose=False)
    for record in event.get("Records"):
        key = record.get("s3", {}).get("object", {}).get("key")
        if key in KEY_MAP:
            KEY_MAP.get(key)(s3, key, stage_calbright.session, prod_calbright.session)
        else:
            raise Exception(f"Unknown file uploaded: {key}")


if __name__ == "__main__":
    from test_event import file_upload

    run(file_upload, None)
