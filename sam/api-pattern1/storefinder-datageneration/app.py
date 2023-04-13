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
# Store data
stores = [
    {"id": 1, "storeName": "Birmingham New Street", "storeAddress": "Station Street, Birmingham, B2 4QA", "storeHours": "09:00-17:00", "storeLocation": "[-1.899670,52.476470]"},
    {"id": 2, "storeName": "Bristol Temple Meads", "storeAddress": "Station Approach, Bristol, BS1 6QF", "storeHours": "09:00-17:00", "storeLocation": "[-2.581166,51.449434]"},
    {"id": 3, "storeName": "Clapham Junction", "storeAddress": "St John's Hill, Clapham, Greater London, SW11 2QP", "storeHours": "09:00-17:00", "storeLocation": "[-0.17154,51.46524]"},
    {"id": 4, "storeName": "Guildford", "storeAddress": "Station Approach, Guildford, GU1 4UT", "storeHours": "09:00-17:00", "storeLocation": "[-0.57996,51.23760]"},
    {"id": 5, "storeName": "Leeds City", "storeAddress": "New Station Street, Leeds, LS1 4DY", "storeHours": "08:00-20:30", "storeLocation": "[-1.54714,53.79523]"},
    {"id": 6, "storeName": "Liverpool Lime Street", "storeAddress": "Lime Street, Liverpool, L1 1JD", "storeHours": "09:00-17:30", "storeLocation": "[-2.97893,53.40845]"},
    {"id": 7, "storeName": "London Bridge", "storeAddress": "Tooley Street, London, SE1 3QX", "storeHours": "08:00-16:30", "storeLocation": "[-0.08765,51.50606]"},
    {"id": 8, "storeName": "London Cannon Street", "storeAddress": "Cannon Street, London, EC4N 6AP", "storeHours": "09:00-17:30", "storeLocation": "[-0.08985,51.51153]"},
    {"id": 9, "storeName": "London Charing Cross", "storeAddress": "The Strand, London, WC2N 5HF", "storeHours": "08:00-18:30", "storeLocation": "[-0.12559,51.50855]"},
    {"id": 10, "storeName": "London Euston", "storeAddress": "Euston Road, London, NW1 2RT", "storeHours": "09:00-17:30", "storeLocation": "[-0.13215,51.52693]"},
    {"id": 11, "storeName": "London Kings Cross", "storeAddress": "Euston Road, London, N1 9AL", "storeHours": "09:00-17:30", "storeLocation": "[-0.12301,51.53044]"},
    {"id": 12, "storeName": "London Liverpool Street", "storeAddress": "Bishopsgate, London, EC2M 7PY", "storeHours": "08:00-16:30", "storeLocation": "[-0.08070,51.51721]"},
    {"id": 13, "storeName": "London Paddington", "storeAddress": "Praed Street, London, W2 1HQ", "storeHours": "09:00-17:30", "storeLocation": "[-0.17898,51.51879]"},
    {"id": 14, "storeName": "London St Pancras International", "storeAddress": "Pancras Road, London, N1C 4QP", "storeHours": "09:00-17:00", "storeLocation": "[-0.12722,51.53146]"},
    {"id": 15, "storeName": "London Victoria", "storeAddress": "Victoria Street, London, SW1V 1JU", "storeHours": "08:30-17:30", "storeLocation": "[-0.14208,51.49552]"},
    {"id": 16, "storeName": "London Waterloo", "storeAddress": "Station Approach, London, SE1 8SW", "storeHours": "08:00-20:30", "storeLocation": "[-0.11532,51.50078]"},
    {"id": 17, "storeName": "Manchester Piccadilly", "storeAddress": "Piccadilly Station Approach, Manchester, M60 7RA", "storeHours": "09:00-17:30", "storeLocation": "[-2.23182,53.47714]"},
    {"id": 18, "storeName": "Reading", "storeAddress": "Station Hill, Reading, RG1 1LZ", "storeHours": "07:00-17:30", "storeLocation": "[-0.97485,51.45869]"}
]

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
