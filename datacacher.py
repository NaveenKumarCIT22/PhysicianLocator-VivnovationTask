import pandas as pd
import sqlite3
import requests
import json
from datetime import datetime
import os
from logger import setup_logger
from load import fetch_physicians
from tqdm import tqdm
import concurrent.futures  # Import concurrent.futures for multithreading

logger = setup_logger('load_logger', 'load.log')


def fetch_all_zips():
    """
    Fetch all unique ZIP codes from the database.
    """
    conn = sqlite3.connect('.\\Datas\\msatozip.db')
    res = pd.read_sql_query("SELECT DISTINCT ZIP FROM data_table", conn)
    return res['ZIP'].tolist()


def cache_physician(postal_code):
    """
    Fetch and cache physician data for a single ZIP code.
    """
    postal_code = str(postal_code).zfill(5)
    fetch_physicians(postal_code)


def cache_all_physicians():
    """
    Fetch and cache physician data for all ZIP codes in the database using multithreading.
    """
    zip_codes = fetch_all_zips()
    logger.info(f"Total ZIP codes to process: {len(zip_codes)}")

    # Use ThreadPoolExecutor to parallelize the API calls
    # Adjust max_workers as needed
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Use tqdm to display a progress bar
        list(tqdm(executor.map(cache_physician, zip_codes),
                  total=len(zip_codes), desc="Caching Physicians"))

    logger.info("Finished caching physicians for all ZIP codes.")


if __name__ == "__main__":
    # To cache all physicians, uncomment the following line:
    cache_all_physicians()

    # Example usage with a specific MSA (you can comment this out if only caching)
    # msa_name = "aguadilla"
    # res = fetch_data(msa_name)
    # zips = res['ZIP'].tolist()
    # logger.info(f"Found {len(zips)} ZIP codes in {msa_name}")
    # all_physicians = []
    # filenames = []
    # for postal_code in zips:
    #     postal_code = str(postal_code).zfill(5)
    #     files = fetch_physicians(postal_code)  # Returns a list of filenames
    #     filenames.extend(files)

    # all_physicians = load_physicians(filenames)
    # logger.info(all_physicians[:3])
    # print(all_physicians[:3])
