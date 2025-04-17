from dagster import AssetExecutionContext, asset
import os
import requests


@asset
def border_crossing_csv(context: AssetExecutionContext):
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

    print("CSV downloaded successfully!")
