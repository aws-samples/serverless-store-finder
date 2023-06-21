""" Lambda function for the API serving incoming store finder requests. """

## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0

import os
import json
import boto3
import botocore
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, CORSConfig

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
# Use AWS Lambda Power Tools' event handler for handling requests
cors_config = CORSConfig(
        allow_origin=AWS_ALLOWED_CORS_ORIGIN_AMPLIFY,
        extra_origins=AWS_ALLOWED_CORS_ORIGINS,
        max_age=300
    )
app = APIGatewayRestResolver(cors=cors_config)

def get_all_store_locations():
    """ Retrieve all store locations from DynamoDB table. """
    # pylint: disable=too-many-locals, unused-argument
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
    return destination_stores

@app.get("/stores")
def get_nearest_stores():
    """ Return all stores. """
    return get_all_store_locations()

@app.post("/stores/nearest")
def post_nearest_stores():
    """ Return nearest stores. """
    destination_stores = get_all_store_locations()
    departure_point = json.loads(app.current_event.body)["Departure"]["Point"]
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
            error_message = "Error: " + str(error.response["Error"])
            print(error_message)
            raise BadRequestError(
                error_message +
                " " +
                "Check Amazon Location Service documentation for location data provider "+
                "restrictions - https://docs.aws.amazon.com/location/latest/developerguide/"+
                "calculate-route-matrix.html#matrix-routing-position-limits"
            )
        except botocore.exceptions.ClientError as error:
            error_message = "Error: " + str(error.response["Error"])
            print(error_message)
            raise Exception(error_message)
    result = 0
    nearest_stores = []
    while result < len(matrix_routing_results):
        nearest_stores.append(
                dict(destination_stores[result], **(matrix_routing_results[result]))
            )
        result += 1
    # Reorder in ascending distance
    nearest_stores.sort(key=lambda x: x["Distance"], reverse=False)
    return nearest_stores[0:int(json.loads(app.current_event.body)["MaxResults"])]

def lambda_handler(event, context):
    """ Lambda handler for incoming requests. """
    return app.resolve(event, context)