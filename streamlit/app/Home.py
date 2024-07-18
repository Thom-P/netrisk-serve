import streamlit as st

st.set_page_config(
    page_title='Home',
    page_icon=None,
    layout="wide",
    initial_sidebar_state="auto",
    menu_items=None
)
# st.sidebar.markdown("# Home")

sidebar_logo = "static/netrisk-serve-hr-logo-transparent.png"
main_body_logo = "static/netrisk-serve-icon-transparent.png"
st.logo(sidebar_logo, icon_image=main_body_logo)

st.markdown("# Netrisk-serve")
st.markdown("### Station management, trace view, and data download")

# st.page_link("Home.py", label="Home", icon="🏠")
st.page_link("pages/10_Stations_and_traces.py", label="Stations", icon="📌")
st.page_link("pages/20_Add_station_XML.py", label="StationXML", icon="📈")
st.page_link("http://seiscomp:8080", label="FDSN Web Service", icon="➡️")
