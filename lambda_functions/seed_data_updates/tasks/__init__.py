import codecs
import csv


def read_s3_csv(s3_client, key):
    data = s3_client.get_object(Bucket="calbright-engineering", Key=key)
    return [row for row in csv.DictReader(codecs.getreader("utf-8")(data["Body"]))]
