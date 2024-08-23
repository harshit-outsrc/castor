# Seed Data Updates

This lambda function reads any file uploaded to s3://calbright-engineering/seed_data/ and attempts to use that data to
upsert data into our Stage and Prod Calbright databases.

## File Data Supported

### COCI Program File
1. Navigate to the [COCI Program Page](https://coci2.ccctechcenter.org/programs) and filter College to Calbright
2. Click the Export to Excel Button in the top right
3. Rename the file to `COCI-Program-Export.csv`
4. Upload that file to [s3://calbright-engineering/seed_data/](https://us-west-2.console.aws.amazon.com/s3/buckets/calbright-engineering?region=us-west-2&bucketType=general&prefix=seed_data/)
5. This will kick of a lambda invocation to ingest the program data into both the stage and prod databases
   
### COCI Course File
1. Navigate to the [COCI Course Page](https://coci2.ccctechcenter.org/courses) and filter College to Calbright
2. Click the Export to Excel Button in the top right
3. Rename the file to `COCI-Course-Export.csv`
4. Upload that file to [s3://calbright-engineering/seed_data/](https://us-west-2.console.aws.amazon.com/s3/buckets/calbright-engineering?region=us-west-2&bucketType=general&prefix=seed_data/)
5. This will kick of a lambda invocation to ingest the course data into both the stage and prod databases

### Staff Data File
1. Download the current [Staff Data](https://us-west-2.console.aws.amazon.com/s3/object/calbright-engineering?region=us-west-2&bucketType=general&prefix=seed_data/staff_data.csv)
2. Make whatever necessary updates are required
3. Upload that file to [s3://calbright-engineering/seed_data/](https://us-west-2.console.aws.amazon.com/s3/buckets/calbright-engineering?region=us-west-2&bucketType=general&prefix=seed_data/)
5. This will kick of a lambda invocation to ingest the staff data into both the stage and prod databases