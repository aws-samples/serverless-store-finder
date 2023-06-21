""" Lambda function for the API serving incoming store finder requests. """

## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0

import os
import json
import boto3
import botocore

# Environment specific parameters pulled from Lambda environment variables
AWS_REGION = os.environ["AWS_REGION"]
AMAZON_DYNAMODB_TABLE = os.environ["AMAZON_DYNAMODB_TABLE"]
AMAZON_LOCATION_SERVICE_ROUTE_CALCULATOR = os.environ["AMAZON_LOCATION_SERVICE_ROUTE_CALCULATOR"]
# Route matrix calculations are batched to take into consideration API limits -
# https://docs.aws.amazon.com/location/latest/developerguide/calculate-route-matrix.html#matrix-routing-longer-routes
AMAZON_LOCATION_SERVICE_MATRIX_ROUTING_BATCH_SIZE = 10
AWS_ALLOWED_CORS_ORIGINS = os.environ["AWS_ALLOWED_CORS_ORIGINS"].split(",")
AWS_ALLOWED_CORS_ORIGIN_AMPLIFY = os.environ["AWS_ALLOWED_CORS_ORIGIN_AMPLIFY"]
# DynamoDB connectivity
dynamodb_client = boto3.resource(
    "dynamodb",
    region_name=AWS_REGION
)
# Initialising AWS SDK clients
table = dynamodb_client.Table(AMAZON_DYNAMODB_TABLE)
location_client = boto3.client("location")
# Lambda execution environment cache to store all stores
all_stores_cache = None

def lambda_handler(event, context):
    """ Lambda handler for GET/POST requests. """
    # pylint: disable=too-many-locals, unused-argument
    # Handle CORS headers
    cors_allow_origin = None
    if event["multiValueHeaders"]["origin"][0] in AWS_ALLOWED_CORS_ORIGINS:
        cors_allow_origin = event["multiValueHeaders"]["origin"][0]
    else:
        # Allow Amplify Hosting URL
        url_string = ".".join(event["multiValueHeaders"]["origin"][0].split('.')[1:4])
        if AWS_ALLOWED_CORS_ORIGIN_AMPLIFY in url_string:
            cors_allow_origin = event["multiValueHeaders"]["origin"][0]
    # Respond to client requests
    response = {}
    if ((event["httpMethod"]=="POST") or (event["httpMethod"]=="GET")):
        # Respond to POST and GET requests
        # Retrieve all possible store locations from DynamoDB table
        # if these do not already exist in the local Lambda execution
        # environment cache
        global all_stores_cache
        if all_stores_cache:
            all_stores = all_stores_cache
            print("Local cache hit! (" + str(len(all_stores_cache)) + " stores)")
        else:
            try:
                scan_paginator = dynamodb_client.meta.client.get_paginator("scan")
                page_iterator = scan_paginator.paginate(
                    TableName=AMAZON_DYNAMODB_TABLE,
                    ProjectionExpression="id,storeName,storeAddress,storeHours,storeDistance,storeLocation"
                )
            except botocore.exceptions.ClientError as error:
                error_message = "Error: " + str(error.response["Error"])
                print(error_message)
                raise Exception(error_message)
            all_stores = []
            for page in page_iterator:
                all_stores.extend(page["Items"])
            all_stores_cache = all_stores
        destination_stores = []
        for store in all_stores:
            destination_stores.append(
                {
                    "id": int(store["id"]),
                    "name": store["storeName"],
                    "address": store["storeAddress"],
                    "hours": store["storeHours"],
                    "location": json.loads(store["storeLocation"])
                }
            )
        # If this is a POST request with a body containing departure point
        if (
            (event["httpMethod"]=="POST") and
            (event["resource"]=="/stores/nearest") and
            event["body"]
        ):
            departure_point = json.loads(event["body"])["Departure"]["Point"]
            matrix_routing_results = []
            for batch in range(
                    0,
                    len(destination_stores),
                    AMAZON_LOCATION_SERVICE_MATRIX_ROUTING_BATCH_SIZE
                ):
                departure_batch = destination_stores[
                        batch:batch+AMAZON_LOCATION_SERVICE_MATRIX_ROUTING_BATCH_SIZE
                    ]
                try:
                    route_matrix_response = location_client.calculate_route_matrix(
                        CalculatorName=AMAZON_LOCATION_SERVICE_ROUTE_CALCULATOR,
                        DeparturePositions=[departure_point],
                        DestinationPositions=[store["location"] for store in departure_batch]
                    )["RouteMatrix"][0]
                    matrix_routing_results.extend(route_matrix_response)
                except location_client.exceptions.ValidationException as error:
                    print(error)
                    response_body = [
                        str(error.response["Error"]) +
                        " " +
                        "Check Amazon Location Service documentation for location data provider "+
                        "restrictions - https://docs.aws.amazon.com/location/latest/developerguide/"+
                        "calculate-route-matrix.html#matrix-routing-position-limits"
                    ]
                    response["statusCode"] = 400
                except botocore.exceptions.ClientError as error:
                    error_message = "Error: " + str(error.response["Error"])
                    print(error_message)
                    raise Exception(error_message)
                else:
                    result = 0
                    response_body = []
                    while result < len(matrix_routing_results):
                        response_body.append(
                                dict(destination_stores[result], **(matrix_routing_results[result]))
                            )
                        result+=1
                    # Reorder in ascending distance
                    response_body.sort(key=lambda x: x["Distance"], reverse=False)
                    response_body = response_body[0:int(json.loads(event["body"])["MaxResults"])]
                    response["statusCode"] = 200
        elif ((event["httpMethod"]=="GET") and (event["resource"]=="/stores")):
            response_body = destination_stores
            response["statusCode"] = 200
    response["body"] = json.dumps(response_body)
    response["headers"] = {
        "Access-Control-Allow-Origin": cors_allow_origin,
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"
    }
    return response
