import os

import pandas
import requests
from dagster import AssetExecutionContext, asset
from pandas import DataFrame
import duckdb


@asset
def bronze_borders_crossing(context: AssetExecutionContext) -> DataFrame:
    context.log.info('Downloading Border Crossing CSV')
    url = "https://data.transportation.gov/api/views/keg4-3bc2/rows.csv?accessType=DOWNLOAD"
    response = requests.get(url)

    # Raise exception if request failed
    response.raise_for_status()

    base_download_path = "temp_data/data_gov/border_crossing"
    os.makedirs(base_download_path, exist_ok=True)

    # Save CSV to a file
    with open(f"{base_download_path}/data.csv", "wb") as f:
        f.write(response.content)

    df = pandas.read_csv(f"{base_download_path}/data.csv")

    return df


@asset
def silver_borders_crossing(context: AssetExecutionContext, bronze_borders_crossing):
    context.log.info('Processing Silver Layer for border_crossing')
    postgres_config = {
        "host": "127.0.0.1",
        "port": 5533,
        "dbname": "operation_db",
        "user": "operation_db",
        "password": "operation_db",
    }
    con = duckdb.connect()

    con.execute("INSTALL postgres;")
    con.execute("LOAD postgres;")

    con.execute(f"""
            ATTACH 'dbname={postgres_config['dbname']} user={postgres_config['user']} 
                    password={postgres_config['password']} host={postgres_config['host']} port={postgres_config['port']}' 
            AS postgres_db (TYPE postgres);
        """)

    table_name = "border_crossing"
    con.execute(f"""
        CREATE TABLE IF NOT EXISTS postgres_db.public.{table_name} AS 
        SELECT * FROM bronze_borders_crossing
    """)
    result_df = con.execute(f"""
            SELECT * FROM postgres_db.public.{table_name};
        """).fetchdf()
    context.log.info("logging data from operation_db")
    context.log.info(result_df)
