""" Lambda function to upload the single CSV file.
This Lambda function is designed to be triggered by CloudFormation as a
custom resource during stack provisioning.
"""

## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0

import json
import cfnresponse

# Reference CSV file bundled with the function code
CSV_FILE_NAME = "us-post-offices.csv"

def lambda_handler(event, context):
    """ Lambda function to upload CSV data file to S3 bucket. """
    response = {}
    print(event)
    if event["RequestType"] == "Delete":
        cfnresponse.send(event, context, cfnresponse.SUCCESS, response)
    if event["RequestType"] == "Create":
        try:
            # Importing modules inside of exception handling to
            # report back to CloudFormation if there are any
            # errors with the import steps
            import os           # pylint: disable=import-outside-toplevel
            import boto3        # pylint: disable=import-outside-toplevel

            # Environment specific parameters pulled from environment variables
            S3_BUCKET = os.environ["S3_BUCKET"]
            # Upload CSV file to S3 bucket
            s3_client = boto3.client("s3")
            print("Uploading file to S3 bucket........")
            s3_client.upload_file(CSV_FILE_NAME, S3_BUCKET, CSV_FILE_NAME)
            print("Uploaded file to S3 bucket........")
            response = {"message": CSV_FILE_NAME + " uploaded to " + S3_BUCKET + "."}
            cfnresponse.send(event, context, cfnresponse.SUCCESS, response)
        # Any exceptions, return a failure back to CloudFormation
        except Exception as error:  # pylint: disable=broad-except
            response = {"message": str(error)}
            cfnresponse.send(event, context, cfnresponse.FAILED, response)
    return json.dumps(response)
