import pandas as pd
from group_physicians import get_groups
from plot_physician_groups import geocode_address, extract_data_from_list, create_map
from load import get_local_physicians, get_all_msa
import streamlit.components.v1 as components
import streamlit as st
from logger import setup_logger

logger = setup_logger('ui_logger', 'ui.log')


def search_physicians(msa_name, msa_code, input_type):
    """
    Search for physicians based on MSA Name or MSA Code.
    """
    logger.info(
        f"Searching physicians with {input_type}: {msa_name if input_type == 'MSA Name' else msa_code}")
    if input_type == "MSA Name":
        return get_local_physicians(msa_name)
    elif input_type == "MSA Code":
        return get_local_physicians(msa_code)
    return None


def display_map(physician_map):
    """
    Display the physician map in Streamlit.
    """
    st.write("## Map:")
    try:
        map_path = "pages/plotly_map.html"
        physician_map.write_html(map_path)
        with open(map_path, "r", encoding="utf-8") as f:
            map_html = f.read()
        components.html(map_html, height=600, width=1000, scrolling=True)
    except Exception as e:
        logger.error(f"Error displaying map: {e}")
        st.error(f"Error displaying map: {e}")


def display_person_groups(person_groups):
    """
    Display the person groups in Streamlit.
    """
    st.write("## Person Groups:")
    person_groups_df = pd.DataFrame(
        list(person_groups.items()), columns=['Physician', 'Groups'])
    st.dataframe(person_groups_df, use_container_width=True)


def main():
    """
    Main function to run the Streamlit app.
    """
    st.title("Physician Locator")
    input_type = st.radio("## Search by:", ("MSA Name", "MSA Code"))
    msa_names_df = get_all_msa()
    msa_names = msa_names_df['Addr'].tolist()
    msa_name = st.selectbox(
        "Enter MSA Name:", options=msa_names) if input_type == "MSA Name" else None
    msa_code = st.text_input(
        "Enter MSA Code:") if input_type == "MSA Code" else None

    if st.button("Search"):
        json_data = search_physicians(msa_name, msa_code, input_type)
        person_groups, data_lst = get_groups(json_data[:30])
        data = extract_data_from_list(data_lst[:30])
        if data is not None and not data.empty:
            physician_map = create_map(data)
            if physician_map:
                display_map(physician_map)
                display_person_groups(person_groups)
            else:
                logger.error("Failed to create map.")
                st.error("Failed to create map.")
        else:
            logger.warning("No physician data to plot.")
            st.warning("No physician data to plot.")


if __name__ == "__main__":
    main()
