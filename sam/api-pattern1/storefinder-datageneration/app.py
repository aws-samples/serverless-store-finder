""" Lambda function to generate store finder data.
This Lambda function is designed to be triggered by CloudFormation as a
custom resource during stack provisioning.
"""

## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0

import json
import cfnresponse

# Reference JSON file bundled with the function code
STORES_JSON_FILE = "stores.json"

def lambda_handler(event, context):
    """ Lambda function for CloudFormation custom resource. """
    response = {}
    if event["RequestType"] == "Delete":
        cfnresponse.send(event, context, cfnresponse.SUCCESS, response)
    if event["RequestType"] == "Create":
        try:
            # Importing modules inside of exception handling to
            # report back to CloudFormation if there are any
            # errors with the import steps
            import os       # pylint: disable=import-outside-toplevel
            import boto3    # pylint: disable=import-outside-toplevel

            # Environment specific parameters pulled from environment variables
            AWS_REGION = os.environ["AWS_REGION"]
            AMAZON_DYNAMODB_TABLE = os.environ["AMAZON_DYNAMODB_TABLE"]
            # DynamoDB connectivity
            dynamodb_client = boto3.resource(
                "dynamodb",
                region_name=AWS_REGION
            )
            table = dynamodb_client.Table(AMAZON_DYNAMODB_TABLE)
            # Load store data from JSON file
            with open(STORES_JSON_FILE) as stores_json:
                stores = json.load(stores_json)
            # Put items into DynamoDB table
            for store in stores:
                table.put_item(
                    Item={
                        "id": store["id"],
                        "storeName": store["storeName"],
                        "storeAddress": store["storeAddress"],
                        "storeHours": store["storeHours"],
                        "storeLocation": store["storeLocation"]
                    }
                )
                print(str(store["storeName"])+" store details added to table.")
            response = {"message": str(len(stores))+" store details added to table"}
            cfnresponse.send(event, context, cfnresponse.SUCCESS, response)
        # Any exceptions, return a failure back to CloudFormation
        except Exception as error:  # pylint: disable=broad-except
            response = {"message": str(error)}
            cfnresponse.send(event, context, cfnresponse.FAILED, response)
    return json.dumps(response)
