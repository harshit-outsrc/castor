file_upload = {
    "Records": [
        {
            "eventVersion": "2.1",
            "eventSource": "aws:s3",
            "awsRegion": "us-west-2",
            "eventTime": "2024-06-27T20:17:31.470Z",
            "eventName": "ObjectCreated:Put",
            "userIdentity": {"principalId": "AWS:AROAXTVVKG7OE5SWNXWFD:brendan.volheim@calbright.org"},
            "requestParameters": {"sourceIPAddress": "52.11.150.178"},
            "responseElements": {
                "x-amz-request-id": "TEW6FXB9AJG3AZNT",
                "x-amz-id-2": "vdmFonieBv+NTfkrmYEBmhexMvm3dYVBaeCDIYd6Jp7T/",
            },
            "s3": {
                "s3SchemaVersion": "1.0",
                "configurationId": "f45e6f67-b455-412c-b5da-13b4d23eb32c",
                "bucket": {
                    "name": "calbright-engineering",
                    "ownerIdentity": {"principalId": "ALHHC4ZG1B1Y0"},
                    "arn": "arn:aws:s3:::calbright-engineering",
                },
                "object": {
                    "key": "seed_data/COCI-Course-Export.csv",
                    "size": 4246,
                    "eTag": "ee43837771c5e3269a7d8d58e89057ca",
                    "sequencer": "00667DC8DB6E1CC2F4",
                },
            },
        }
    ]
}
