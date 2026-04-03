import json
import os
import boto3
from datetime import datetime

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
    extracts metadata from S3 upload events received via SNS.
    logs file information to CloudWatch and writes a JSON metadata
    file to the processed/metadata/ prefix in the same bucket.

    event structure (SNS wraps the S3 event):
    {
        "Records": [{
            "Sns": {
                "Message": "{\"Records\":[{\"s3\":{...}}]}"  # this is a JSON string!
            }
        }]
    }

    required log format:
        [METADATA] File: {key}
        [METADATA] Bucket: {bucket}
        [METADATA] Size: {size} bytes
        [METADATA] Upload Time: {timestamp}

    required S3 output:
        writes a JSON file to processed/metadata/{filename}.json containing:
        {
            "file": "{key}",
            "bucket": "{bucket}",
            "size": {size},
            "upload_time": "{timestamp}"
        }
    """

    print("=== metadata extractor invoked ===")

    # loop through event['Records']
    for record in event['Records']:
        # for each record, get the SNS message string from record['Sns']['Message']
        msg = record['Sns']['Message']

        # parse the SNS message string as JSON to get the S3 event
        s3_event = json.loads(msg)

        # loop through the S3 event's 'Records'
        for s3_record in s3_event['Records']:
            # extract bucket name from s3_record['s3']['bucket']['name']
            bucket = s3_record['s3']['bucket']['name']

            # extract object key from s3_record['s3']['object']['key']
            key = s3_record['s3']['object']['key']

            # extract file size from s3_record['s3']['object']['size']
            size = s3_record['s3']['object']['size']

            # extract event time from s3_record['eventTime']
            event_time = s3_record['eventTime']

            print(f"[METADATA] File: {key}")
            print(f"[METADATA] Bucket: {bucket}")
            print(f"[METADATA] Size: {size} bytes")
            print(f"[METADATA] Upload Time: {event_time}")
            
            # build a metadata dict with file, bucket, size, upload_time
            metadata = {"file": key, "bucket": bucket, "size": size, "upload_time": event_time}
            
            # get the filename from the key (e.g. "uploads/test.jpg" -> "test")
            filename = os.path.splitext(key.split('/')[-1])[0]

            # write the metadata dict as JSON to s3 at processed/metadata/{filename}.json
            s3.put_object(
                Bucket=bucket,
                Key=f"processed/metadata/{filename}.json",
                Body=json.dumps(metadata),
                ContentType="application/json"
            )

    #       hint: s3.put_object(Bucket=bucket, Key=f"processed/metadata/{filename}.json",
    #             Body=json.dumps(metadata), ContentType='application/json'))

    return {'statusCode': 200, 'body': 'metadata extracted'}
