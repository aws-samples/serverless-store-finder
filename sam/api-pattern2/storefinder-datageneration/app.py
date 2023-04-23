## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0
import os
import json
import boto3
import psycopg2
from psycopg2 import extras
import pandas as pd

s3_client = boto3.client("s3")
sm_client = boto3.client("secretsmanager")
rds_endpoint = os.environ["RDS_ENDPOINT"]
rds_table = os.environ["RDS_TABLE_NAME"]
secret_name = os.environ["SECRET_ID"]
### define DB secrets
secret = sm_client.get_secret_value(
      SecretId=secret_name)
secret_dict = json.loads(secret["SecretString"])
username = secret_dict["username"]
password = secret_dict["password"]

def lambda_handler(event, context):
    ### get object from s3 and read the data
    source_bucket = event["Records"][0]["s3"]["bucket"]["name"]
    source_object = event["Records"][0]["s3"]["object"]["key"]
    response = s3_client.get_object(Bucket=source_bucket, Key=source_object)
    def execute_values(conn, data_frame, table):
        tuples = [tuple(x) for x in data_frame.to_numpy()]
        cols = ','.join(list(data_frame.columns))
        # SQL query to execute
        query = "INSERT INTO %s(%s) VALUES %%s" % (table, cols)
        cursor = conn.cursor()
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
        cursor.close()
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
    # Dropping PostOffice table if already exists.
    cursor.execute("DROP TABLE IF EXISTS "+rds_table)
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
    execute_values(conn, data_frame, rds_table)
