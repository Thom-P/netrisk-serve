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
stat_and_traces = st.Page("app_pages/10_Stations_and_traces.py",
                          title="Stations and traces", icon="📌")
add_xml = st.Page("app_pages/20_Add_station_XML.py",
                  title="Create new station XML", icon="✏️")
list_xml = st.Page("app_pages/21_List_station_XML.py",
                   title="Manage XML files", icon="📁")
ftp_accounts = st.Page("app_pages/30_Station_FTP_account.py",
                       title="Manage FTP accounts", icon="📡")

# Get current page though navigation (first one is default)
pg = st.navigation(
        [stat_and_traces, ftp_accounts, list_xml, add_xml]
        # {
        #     "Stations and Traces": [stat_and_traces],
        #     "Station XML files": [add_xml, list_xml],
        #     "FTP accounts": [ftp_accounts],
        # }
    )
pg.run()
