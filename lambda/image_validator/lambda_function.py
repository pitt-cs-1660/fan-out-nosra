import json
import os
import boto3

s3 = boto3.client('s3')

VALID_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif']

def is_valid_image(key):
    """check if the file has a valid image extension."""
    _, ext = os.path.splitext(key.lower())
    return ext in VALID_EXTENSIONS

def lambda_handler(event, context):
    """
    validates that uploaded files are images.
    raises exception for invalid files (triggers DLQ).

    for valid files, copies the object to the processed/valid/ prefix
    in the same bucket so grading can verify output via S3.
    """

    print("=== image validator invoked ===")

    # loop through event['Records']
    for record in event['Records']:
        # get the SNS message string from record['Sns']['Message']
        msg = record['Sns']['Message']
        
        # parse the SNS message string as JSON to get the S3 event
        s3_event = json.loads(msg)
        
        # loop through the S3 event's 'Records'
        for s3_record in s3_event['Records']:
            # extract bucket name and object key
            bucket = s3_record['s3']['bucket']['name']
            key = s3_record['s3']['object']['key']
            
            # use is_valid_image() to check the file extension
            if is_valid_image(key):
                # print the [VALID] message
                print(f"[VALID] {key} is a valid image file")
                
                # get the filename from the key (e.g. "uploads/test.jpg" -> "test.jpg")
                filename = key.split('/')[-1]
                
                # copy the object to processed/valid/{filename}
                s3.copy_object(
                    Bucket=bucket, 
                    Key=f"processed/valid/{filename}",
                    CopySource={'Bucket': bucket, 'Key': key}
                )
            else:
                # print the [INVALID] message
                print(f"[INVALID] {key} is not a valid image type")
                
                # raise ValueError to trigger DLQ
                raise ValueError(f"Invalid file type uploaded: {key}")

    return {'statusCode': 200, 'body': 'validation complete'}
