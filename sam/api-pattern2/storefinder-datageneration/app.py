""" Lambda function to generate store finder data.
Function is designed to be invoked via an Amazon S3 event
notification when a file is uploaded.
"""

## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0

import os
import json
import boto3
import psycopg2
from psycopg2 import extras
import pandas as pd

# AWS SDK clients
s3_client = boto3.client("s3")
sm_client = boto3.client("secretsmanager")
# Environment specific parameters pulled from environment variables
rds_endpoint = os.environ["RDS_ENDPOINT"]
rds_table = os.environ["RDS_TABLE_NAME"]
secret_name = os.environ["SECRET_ID"]
# Define DB secrets
secret = sm_client.get_secret_value(
      SecretId=secret_name)
secret_dict = json.loads(secret["SecretString"])
username = secret_dict["username"]
password = secret_dict["password"]

def execute_values(conn, cursor, data_frame, table):
    """ Insert store data into PostgreSQL database table """
    tuples = [tuple(x) for x in data_frame.to_numpy()]
    cols = ','.join(list(data_frame.columns))
    # SQL query to execute
    query = "INSERT INTO %s(%s) VALUES %%s" % (table, cols)
    try:
        print("EXTRAS", extras.execute_values(cursor, query, tuples))
        extras.execute_values(cursor, query, tuples)
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error: {error}")
        conn.rollback()
        cursor.close()
    print("the dataframe is inserted")
    cursor.execute("UPDATE "
      +rds_table+
      " SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326);"
      )
    conn.commit()
    sql = "SELECT count(*) from "+rds_table+";"
    cursor.execute(sql)
    number_of_rows = int(cursor.fetchone()[0])
    cursor.close()
    return number_of_rows

def lambda_handler(event, context):
    """ Lambda function for data generation using uploaded CSV in S3 bucket. """
    # Get object from s3 and read the data
    source_bucket = event["Records"][0]["s3"]["bucket"]["name"]
    source_object = event["Records"][0]["s3"]["object"]["key"]
    response = s3_client.get_object(Bucket=source_bucket, Key=source_object)
    data = pd.read_csv(response.get("Body"))
    columns_to_drop = ["AltName",
                       "OrigName",
                       "County1",
                       "County2",
                       "County3",
                       "StampIndex",
                       "ID",
                       "Duration",
                       "Established",
                       "Discontinued",
                       "GNIS.Match",
                       "GNIS.Name",
                       "GNIS.County",
                       "GNIS.State",
                       "GNIS.FEATURE_ID",
                       "GNIS.Feature.Class",
                       "GNIS.OrigCounty",
                       "GNIS.Latitude",
                       "GNIS.Longitude",
                       "GNIS.ELEV_IN_M",
                       "GNIS.Dist"]
    data_frame = pd.DataFrame(data)
    data_frame = data_frame.loc[data_frame.Coordinates, :]
    data_frame = data_frame.drop(columns=columns_to_drop)
    data_frame = data_frame.rename({"GNIS.OrigName":"place_name"}, axis="columns")
    conn = psycopg2.connect(
                database="postgres",
                user=username,
                password=password,
                host=rds_endpoint,
                port="5432"
    )
    # Creating a cursor object using the cursor() method
    cursor = conn.cursor()
    # Dropping PostOffice table and extension if already exist
    sql = '''DROP TABLE IF EXISTS '''+rds_table+''';
        DROP EXTENSION IF EXISTS postgis;
        '''
    cursor.execute(sql)
    # Creating table as per requirement
    sql = '''CREATE TABLE '''+rds_table+ ''' (
           name varchar(255),
           state varchar(3),
           origCounty varchar(50),
           continuous boolean,
           place_name varchar(255),
           coordinates boolean,
           latitude double precision,
           longitude double precision
           );
        CREATE EXTENSION postgis;
        ALTER TABLE '''+rds_table+''' ADD COLUMN geom geometry(Point, 4326);
        '''
    cursor.execute(sql)
    print("Table created successfully........")
    number_of_stores = execute_values(conn, cursor, data_frame, rds_table)
    print(str(number_of_stores)+" records successfully inserted........")
    # Remove S3 file and bucket afterwards
    s3_client.delete_object(Bucket=source_bucket, Key=source_object)
    s3_client.delete_bucket(Bucket=source_bucket)
    print("Removed uploaded file and S3 bucket........")
