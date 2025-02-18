# Physician Locator

## Overview

The Physician Locator is a Streamlit-based application designed to help users find physicians based on location. It provides a user-friendly interface for searching and displaying physician information, making it easier for patients to connect with healthcare providers.

## Features

- **Search Functionality:** Allows users to search for physicians based on location.
- **Interactive Map:** Displays physician locations on an interactive map for easy visualization.
- **Detailed Profiles:** Provides detailed information about each physician, including address, and specialties.
- **User-Friendly Interface:** Built with Streamlit for a simple and intuitive user experience.

## Getting Started

### Prerequisites

- Python 3.7+
- Streamlit
- Plotly
- Geopy
- Geopandas
- Pandas

### Installation

1.  Clone the repository:

    ```bash
    git clone https://github.com/NaveenKumarCIT22/PhysicianLocator-VivnovationTask PhysicianLocator
    ```

2.  Navigate to the project directory:

    ```bash
    cd PhysicianLocator
    ```

3.  Create a virtual environment (recommended):

    ```bash
    python -m venv .venv
    ```

    - Activate the virtual environment:

      - **Windows:**

        ```bash
        .venv\Scripts\activate
        ```

      - **macOS/Linux:**

        ```bash
        source .venv/bin/activate
        ```

4.  Install the dependencies:

    ```bash
    pip install -r requirements.txt
    ```

### Usage

To run the application, use the following command:

```bash
streamlit run ui.py
```

![alt text](image.png)
ComboBox selection for MSA name or MSA code

![alt text](image-1.png)
Plotted Map with info tooltip

![alt text](image-2.png)
Physician and Physician Group mapping

## Contact

- Naveen Kumar M - [naveenkumarm.innovator](naveenkumarm.innovator@gmail.com)
- GITHUB - [NaveenKumarCIT22](https://github.com/NaveenKumarCIT22/)
