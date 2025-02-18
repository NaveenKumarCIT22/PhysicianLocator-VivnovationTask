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
    """
    for attempt in range(max_retries):
        try:
            locs = gpd.tools.geocode(
                address, provider=provider, user_agent="myGeocoder", timeout=10)
            if not locs.empty and not locs.geometry.isnull().any() and not (locs.geometry.iloc[0] is None):
                if not locs.geometry.iloc[0].is_empty:
                    return locs.geometry.iloc[0].x, locs.geometry.iloc[0].y
                else:
                    return None
            else:
                return None
        except (GeocoderTimedOut, GeocoderServiceError, MaxRetryError, NewConnectionError) as e:
            logger.error(f"Geocoding error for {address}: {e}")
        except Exception as e:
            logger.error(f"Geocoding error for {address}: {e}")
        if attempt < max_retries - 1:
            delay = initial_delay * (2 ** attempt)
            time.sleep(delay)
    return None


def extract_data_from_list(data_list):
    """
    Extracts data from a list of dictionaries, geocodes addresses, and returns a Pandas DataFrame.
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
            continue

        coordinates = geocode_address(address, provider='arcgis')
        if not coordinates:
            continue

        records.append({
            "Name/Group": name,
            "Specialty": specialties,
            "Address": address,
            "Latitude": coordinates[1],
            "Longitude": coordinates[0]
        })

    return pd.DataFrame(records)


def create_map(df):
    """
    Creates an interactive map using plotly.express with enhanced features.
    """
    if df.empty:
        logger.warning("No data to display on the map.")
        return None

    fig = px.scatter_mapbox(
        df,
        lat="Latitude",
        lon="Longitude",
        hover_name="Name/Group",
        hover_data={"Specialty": True, "Address": True},
        color_discrete_sequence=["green"],
        zoom=10,
        height=600,
        width=1000
    )

    fig.update_traces(marker=dict(size=12, symbol='circle', opacity=0.7))

    fig.update_layout(
        mapbox_style="carto-positron",
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
