""" Lambda function (custom resource) to generate store finder data. """

import os
import json
import boto3
import cfnresponse

# Environment specific parameters pulled from environment variables.
AWS_REGION = os.environ["AWS_REGION"]
AMAZON_DYNAMODB_TABLE = os.environ["AMAZON_DYNAMODB_TABLE"]
# DynamoDB connectivity
dynamodb_client = boto3.resource(
    "dynamodb",
    region_name=AWS_REGION
)
table = dynamodb_client.Table(AMAZON_DYNAMODB_TABLE)
STORES_JSON_FILE = "stores.json"

# Load store data from JSON file
with open(STORES_JSON_FILE) as stores_json:
    stores = json.load(stores_json)

def lambda_handler(event, context):
    """ Lambda function for CloudFormation custom resource. """
    response = {}
    if event["RequestType"] == "Delete":
        cfnresponse.send(event, context, cfnresponse.SUCCESS, response)
    if event["RequestType"] == "Create":
        try:
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
        except Exception as error:
            response = {"message": str(error)}
            cfnresponse.send(event, context, cfnresponse.FAILED, response)
    return json.dumps(response)
