"""Entry point for the Netrisk-serve Streamlit UI."""

import streamlit as st

from utils.style import apply_style_tweaks

# This is common to all pages
st.set_page_config(
    layout="wide",
    initial_sidebar_state="auto",
    menu_items=None
)
sidebar_logo = "static/netrisk-serve-hr-logo-transparent.png"
main_body_logo = "static/netrisk-serve-icon-transparent.png"
st.logo(sidebar_logo, icon_image=main_body_logo)
apply_style_tweaks()

# Pages declaration
stat_and_traces = st.Page("app_pages/stations_and_traces.py",
                          title="Stations and traces", icon="📌")
add_xml = st.Page("app_pages/add_station_XML.py",
                  title="Create new station XML", icon="✏️")
list_xml = st.Page("app_pages/list_station_XML.py",
                   title="Manage XML files", icon="📁")
ftp_accounts = st.Page("app_pages/station_FTP_account.py",
                       title="Manage FTP accounts", icon="📡")

# Get the current page through navigation and run the associated script
# (first page runs as default)
pg = st.navigation(
        [stat_and_traces, ftp_accounts, list_xml, add_xml]
        # or to use subcategories:
        # {
        #     "Stations and Traces": [stat_and_traces],
        #     "Station XML files": [add_xml, list_xml],
        #     "FTP accounts": [ftp_accounts],
        # }
    )
try:
    pg.run()
except Exception as e:
    st.error(f"Unexpected error: {e}", icon="🚨")
    st.stop()
