
import boto3
import csv
import io


AWS_PROFILE = "validation-agent"
AWS_REGION = "ap-south-1"


def read_source_data(bucket_name, object_key):
    session = boto3.Session(
        profile_name=AWS_PROFILE,
        region_name=AWS_REGION
    )

    s3_client = session.client("s3")

    response = s3_client.get_object(
        Bucket=bucket_name,
        Key=object_key
    )

    csv_content = response["Body"].read().decode("utf-8")
    records = list(csv.DictReader(io.StringIO(csv_content)))

    return records
