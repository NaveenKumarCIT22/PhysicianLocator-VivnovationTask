import pandas as pd
import geopandas as gpd
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from urllib3.exceptions import MaxRetryError, NewConnectionError
import time
import plotly.express as px
from logger import setup_logger

logger = setup_logger('plot_physician_groups_logger',
                      'plot_physician_groups.log')


def geocode_address(address, max_retries=3, initial_delay=1, provider='nominatim'):
    """
    Geocodes an address and returns the location using geopandas with retry logic.

    Args:
        address (str): The address to geocode.
        max_retries (int): Maximum number of retries.
        initial_delay (int): Initial delay in seconds between retries.

    Returns:
        tuple: A tuple containing (longitude, latitude) if geocoding is successful,
               None otherwise.
    """
    for attempt in range(max_retries):
        try:
            locs = gpd.tools.geocode(
                address, provider=provider, user_agent="myGeocoder", timeout=10)
            if not locs.empty and not locs.geometry.isnull().any() and not (locs.geometry.iloc[0] is None):
                if not locs.geometry.iloc[0].is_empty:
                    return locs.geometry.iloc[0].x, locs.geometry.iloc[0].y
                else:
                    print(
                        f"Geocoding failed for {address[:10]}... - Empty geometry")
                    return None
            else:
                print(f"Geocoding failed for {address[10:]}...")
                return None
        except (GeocoderTimedOut, GeocoderServiceError, MaxRetryError, NewConnectionError) as e:
            logger.error(f"Geocoding error for {address}: {e}")
            print(f"Geocoding error for {address}: {e}")
        except Exception as e:
            logger.error(f"Geocoding error for {address}: {e}")
            print(f"Geocoding error for {address}: {e}")
        if attempt < max_retries - 1:
            delay = initial_delay * (2 ** attempt)
            print(f"Retrying in {delay} seconds...")
            time.sleep(delay)
    return None


def extract_data_from_list(data_list):
    """
    Extracts data from a list of dictionaries, geocodes addresses, and
returns a Pandas DataFrame.

    Args:
        data_list (list): A list of dictionaries, where each dictionary
                           contains physician/group information.  Each dict
                           should have keys like 'address', 'full_name',
                           'organization_name', and 'specialties'.

    Returns:
        pandas.DataFrame: A DataFrame containing the extracted and geocoded data.
                          Returns an empty DataFrame if the input list is empty
                          or if geocoding fails for all entries.
    """
    records = []
    if not data_list:
        return pd.DataFrame(records)

    for record in data_list:
        address = record.get('address')
        full_name = record.get('full_name')
        organization_name = record.get('organization_name')
        specialties = record.get('specialties')
        name = organization_name if organization_name else full_name

        if not address:
            print("Missing address. Skipping record.")
            continue

        coordinates = geocode_address(address, provider='arcgis')
        if not coordinates:
            print(f"Geocoding failed for {address}. Skipping record.")
            continue

        records.append({
            "Name/Group": name,
            "Specialty": specialties,
            "Address": address,
            "Latitude": coordinates[1],
            "Longitude": coordinates[0]
        })

    if not records:
        print("No records could be geocoded.")

    return pd.DataFrame(records)


def create_map(df):
    """
    Creates an interactive map using plotly.express with enhanced features.

    Args:
        df (pd.DataFrame): DataFrame containing physician data with Latitude and Longitude columns.

    Returns:
        plotly.graph_objects.Figure: The plotly map figure.
    """
    if df.empty:
        logger.warning("No data to display on the map.")
        print("No data to display on the map.")
        return None

    center_lat = df["Latitude"].mean()
    center_lon = df["Longitude"].mean()

    fig = px.scatter_mapbox(
        df,
        lat="Latitude",
        lon="Longitude",
        hover_name="Name/Group",
        hover_data={"Specialty": True, "Address": True},
        color_discrete_sequence=["green"],
        zoom=10,
        height=600,
        width=1000,
        center=dict(lat=center_lat, lon=center_lon)
    )

    fig.update_traces(marker=dict(size=12, symbol='circle', opacity=0.7))

    fig.update_layout(
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Rockwell"
        ),
        mapbox=dict(
            zoom=10,
            center=dict(lat=df["Latitude"].mean(), lon=df["Longitude"].mean()),
            pitch=0,
            bearing=0
        )
    )

    fig.update_layout(
        mapbox_zoom=10,
        mapbox_center_lat=df["Latitude"].mean(),
        mapbox_center_lon=df["Longitude"].mean(),
        dragmode='zoom',
    )

    return fig


if __name__ == "__main__":
    input_data = [{'address': 'AVE OSVALDO MOLINA #151, FAJARDO, PR 007383614',
                   'full_name': 'CARLOS AGAPITO FONTANEZ',
                   'organization_name': 'CARLOS AGAPITO FONTANEZ',
                   'specialties': 'Internal Medicine'}]

    data = extract_data_from_list(input_data)

    if not data.empty:
        physician_map = create_map(data)
        if physician_map:
            physician_map.write_html("physician_map.html")
    else:
        logger.warning("No physician data to plot.")
        print("No physician data to plot.")
