import os

import pandas
import requests
from dagster import AssetExecutionContext, asset
from pandas import DataFrame
import duckdb

postgres_config = {
    "host": "127.0.0.1",
    "port": 5533,
    "dbname": "operation_db",
    "user": "operation_db",
    "password": "operation_db",
}

postgres_report_config = {
    "host": "127.0.0.1",
    "port": 5534,
    "dbname": "report_db",
    "user": "report_db",
    "password": "report_db",
}

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
def silver_borders_crossing(context: AssetExecutionContext, bronze_borders_crossing) -> DataFrame:
    context.log.info('Processing Silver Layer for border_crossing')
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
    return result_df


@asset
def gold_borders_crossing_total_migration_by_port_code(context: AssetExecutionContext, silver_borders_crossing):
    context.log.info('Processing Gold Layer for border_crossing')
    con = duckdb.connect()

    con.execute("INSTALL postgres;")
    con.execute("LOAD postgres;")

    con.execute(f"""
            ATTACH 'dbname={postgres_report_config['dbname']} user={postgres_report_config['user']} 
                    password={postgres_report_config['password']} host={postgres_report_config['host']} port={postgres_report_config['port']}' 
            AS postgres_db (TYPE postgres);
        """)

    table_name = "total_migration_by_port_code"
    con.execute(f"""
        CREATE TABLE IF NOT EXISTS postgres_db.public.{table_name} (
            state VARCHAR(250) not null,
            port_code VARCHAR(250) not null,
            border VARCHAR(250) not null,
            value INTEGER not null
        )
    """)
    
    table_name_1 = "filtered_border_crossing"
    con.execute(f"""
        CREATE TABLE IF NOT EXISTS postgres_db.public.{table_name_1} (
            port_name VARCHAR(250) not null,
            state VARCHAR(250) not null,
            port_code VARCHAR(250) not null,
            latitude DECIMAL(10,6) not null,
            longitude DECIMAL(10,6) not null,
            border VARCHAR(250) not null,
            measure VARCHAR(250) not null,
            value INTEGER not null,
            date DATE
            
        )
    """)

    con.execute(f"""
        INSERT INTO postgres_db.public.{table_name} (value, state, port_code, border)
        SELECT SUM("Value") as value, "State" as state, "Port Code" as port_code, "Border" as border
        FROM silver_borders_crossing
        GROUP BY "State", "Port Code", "Border"
    """)
    
    con.execute(f"""
        INSERT INTO postgres_db.public.{table_name_1} (value, port_name, state, port_code, border, measure, latitude, longitude, date)
        SELECT SUM("Value") AS value, "Port Name" as port_name, "State" as state, "Port Code" as port_code, 
        "Border" as border, "Measure" as measure, "Latitude" as latitude, "Longitude" as longitude, STRPTIME("Date", '%b %Y') as date 
        FROM silver_borders_crossing
        Group BY  "Port Name", "State", "Port Code", "Border", "Measure","Longitude", "Latitude","Date"
    """)