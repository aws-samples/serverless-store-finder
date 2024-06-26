""" Lambda function for the API serving incoming store finder requests. """

## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0

import os
import json
import operator
import psycopg2
import boto3
import botocore.exceptions
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, CORSConfig
from aws_lambda_powertools.event_handler.exceptions import BadRequestError, InternalServerError

### Get Environment Variables
AWS_ALLOWED_CORS_ORIGINS = os.environ["AWS_ALLOWED_CORS_ORIGINS"].split(",")
AWS_ALLOWED_CORS_ORIGIN_AMPLIFY = os.environ["AWS_ALLOWED_CORS_ORIGIN_AMPLIFY"]
rds_endpoint = os.environ["RDS_ENDPOINT"]
table_name = os.environ["RDS_TABLE_NAME"]
route_calculator = os.environ["LOCATION_ROUTE_CALCULATOR"]
### Create Boto3 clients
location_client = boto3.client("location")
sm_client = boto3.client("secretsmanager")
### Get DBSecrets
secret_name = os.environ["SECRET_ID"]
secret = sm_client.get_secret_value(
    SecretId=secret_name)
secret_dict = json.loads(secret["SecretString"])
username = secret_dict["username"]
password = secret_dict["password"]
keys = ["id", "name", "hours", "location", "Distance", "DurationSeconds"]
# Use AWS Lambda Power Tools' event handler for handling requests
cors_config = CORSConfig(
        allow_origin=AWS_ALLOWED_CORS_ORIGIN_AMPLIFY,
        extra_origins=AWS_ALLOWED_CORS_ORIGINS,
        max_age=300
    )
app = APIGatewayRestResolver(cors=cors_config)

@app.post("/stores/nearest")
def post_nearest_stores():
    """ Return nearest stores. """
    body = json.loads(app.current_event.body)
    point = body["Departure"]["Point"]
    max_results = int(body["MaxResults"])
    ### Set Global Variables (Set Radius Value, Reformat coordinates for PostGIS)
    radius = str(25)
    formatted_point = point[0], point[1]
    centroid = str(point)
    centroid = centroid.replace("[","(")
    centroid = centroid.replace("]",")")
    ### Establishing the connection to DB
    conn = psycopg2.connect(
        database="postgres", user=username, password=password, host=rds_endpoint, port="5432"
    )
    ### Creating a cursor object using the cursor() method
    cursor = conn.cursor()
    ### Executing an PostgreSQL function using the execute() method
    try:
        #PostGIS query to find all locations within X mile radius of centroid
        cursor.execute(
                        "SELECT place_name, origCounty, state, latitude, longitude, ST_DistanceSphere(geom, ST_MakePoint"
                        +centroid+
                        ")/1000 dist_km FROM "
                        +table_name+
                        " WHERE ST_DistanceSphere(geom, ST_MakePoint"
                        +centroid+
                        ") <="
                        +radius+
                        "* 1609.34;")
    except (Exception, psycopg2.DatabaseError) as error:
        error_message = "Error: " + str(error)
        print(error_message)
        raise InternalServerError(error_message)
    data = cursor.fetchall()
    conn.close()
    ### Deduplicate query results
    data = [*set(data)]
    ### Collect all the radial distance values from the PostgreSQL query (Need to fix)
    i = 0
    distances = {}
    for element in data:
        distances[i]= data[i][5]
        i+=1
    ### Sort the distances from PostgreSQL from shortest to longest radial distance
    sorted_distances = (sorted(distances.items(), key=operator.itemgetter(1)))[0:10]
    index = [i[0] for i in sorted_distances]
    nearest_point_data = [data[i] for i in index]
    ### Get the coordinates of the 25 closest radial distances
    store_coordinates = [nearest_point_data[n][3:5] for n in range(len(sorted_distances))]
    destinations = [(i[1], i[0]) for i in store_coordinates]
    points = tuple(formatted_point)
    origin = []
    origin.append(points)
    ### Call location service Route Matrix for the Top 25 radial distances
    try:
        dm_response = location_client.calculate_route_matrix(
                        CalculatorName=route_calculator,
                        CarModeOptions={"AvoidFerries": True, "AvoidTolls": True},
                        DeparturePositions=origin,
                        DestinationPositions=destinations,
                        TravelMode="Car",
                        DistanceUnit="Kilometers")
    except botocore.exceptions.ClientError as error:
        error_message = "Error: " + str(error.response["Error"])
        print(error_message)
        raise InternalServerError(error_message)
    route_matrix = dm_response["RouteMatrix"]
    indexer = 0
    full_data = []
    for i in nearest_point_data:
        i = list(i)
        try:
            i.append(route_matrix[0][indexer]["Distance"])
        except:
            i.append(int(100000))
        try:
            i.append(int(route_matrix[0][indexer]["DurationSeconds"]))
        except:
            i.append(int(100000))
        indexer+=1
        full_data.append(i)
    def Sort(sub_li):
        # reverse = None (Sorts in Ascending order)
        # key is set to sort using second element of
        # sublist lambda has been used
        sub_li.sort(key=lambda x: x[6])
        return sub_li
    values = Sort(full_data)
    k = 0
    next_closest = []
    closest_locations = []
    for n in range(len(values)):
        next_closest.append(k+1)
        next_closest.append(
            str(values[n][0:3]).replace("'", "").replace("[","").replace("]", ""))
        ### Hard code store hours because not included in dataset
        next_closest.append("08:00-20:30")
        z = (values[n][3:5])
        z[0],z[1] = z[1],z[0]
        next_closest.append(z)
        next_closest.append(str(values[n][6]))
        next_closest.append(str(values[n][7]))
        k+=1
        closest_locations.append(next_closest)
        next_closest = []
    if len(closest_locations)<4:
        nearest_stores = [dict(zip(keys, closest_locations[n])) for n in range(len(closest_locations))]
    else:
        nearest_stores = [dict(zip(keys, closest_locations[n])) for n in range(max_results)]
    return nearest_stores

def lambda_handler(event, context):
    """ Lambda handler for incoming requests. """
    return app.resolve(event, context)