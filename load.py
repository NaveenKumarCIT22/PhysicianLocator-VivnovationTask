import pandas as pd
import sqlite3
import requests
import json
from datetime import datetime
import os
from logger import setup_logger

logger = setup_logger('load_logger', 'load.log')


def fetch_data(msa):
    """
    Fetch data from the database based on MSA name or code.
    """
    conn = sqlite3.connect('.\\Datas\\msatozip.db')
    try:
        msa = int(msa)
        res = pd.read_sql_query(
            f"SELECT * FROM data_table where MSA={msa}", conn)
    except ValueError:
        msa = msa.upper()
        res = pd.read_sql_query(
            f"SELECT * FROM data_table WHERE UPPER(Addr) LIKE '%{msa}%'", conn)
    return res


def fetch_physicians(postal_code):
    """
    Fetch physician data from the API based on postal code.
    """
    all_physicians = []
    filename = f".\\physicians\\{postal_code}.json"

    if os.path.exists(filename):
        logger.info(f"Cache hit! Returning existing file: {filename}")
        return [filename]

    url = f"https://npiregistry.cms.hhs.gov/api/?postal_code={postal_code}&version=2.1&limit=20"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        results = data.get('results', [])
        all_physicians.extend(results)
    else:
        logger.error(f"Request failed with status code {response.status_code}")
        return []

    try:
        with open(filename, 'w') as f:
            json.dump(all_physicians, f)
            logger.info(f"Data written to file: {filename}")
    except Exception as e:
        logger.error(f"Error writing data to file: {e}")
        return []

    return [filename]


def load_physicians(filenames):
    """
    Load physician data from JSON files.
    """
    all_physicians = []
    for filename in filenames:
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                all_physicians.extend(data)
        except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
            logger.error(f"Error loading data from {filename}: {e}")
            continue
    logger.info(f"Loaded {len(all_physicians)} physicians")
    return all_physicians


def get_local_physicians(msa):
    """
    Get local physicians based on MSA name or code.
    """
    res = fetch_data(msa)
    zips = res['ZIP'].tolist()
    logger.info(f"Found {len(zips)} ZIP codes in {msa}")
    all_physicians = []
    filenames = []
    for postal_code in zips:
        postal_code = str(postal_code).zfill(5)
        logger.info(f"Fetching physicians for {postal_code}")
        files = fetch_physicians(postal_code)
        filenames.extend(files)
    all_physicians = load_physicians(filenames)
    return all_physicians


def get_all_msa():
    """
    Get all MSA names.

    Returns:
        pandas.DataFrame: A DataFrame with one column, 'Addr', containing all MSA names.
    """
    conn = sqlite3.connect('.\\Datas\\msatozip.db')
    res = pd.read_sql_query("SELECT Addr FROM data_table", conn)
    return res


if __name__ == "__main__":
    # Replace with actual MSA name or ID
    msa_name = "aguadilla"
    # msa_name = 21940
    res = fetch_data(msa_name)  # 21940, 14460
    zips = res['ZIP'].tolist()
    logger.info(f"Found {len(zips)} ZIP codes in {msa_name}")
    all_physicians = []
    filenames = []
    for postal_code in zips:
        postal_code = str(postal_code).zfill(5)
        files = fetch_physicians(postal_code)  # Returns a list of filenames
        filenames.extend(files)

    all_physicians = load_physicians(filenames)
    logger.info(all_physicians[:3])
    print(all_physicians[:3])
