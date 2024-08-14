import streamlit as st

# this will be common to all pages
st.set_page_config(
    layout="wide",
    initial_sidebar_state="auto",
    menu_items=None
)

sidebar_logo = "static/netrisk-serve-hr-logo-transparent.png"
main_body_logo = "static/netrisk-serve-icon-transparent.png"
st.logo(sidebar_logo, icon_image=main_body_logo)

# Hacky patch to remove +/- buttons on number inputs causing instabilities
# on repetitive clicks
# https://github.com/streamlit/streamlit/issues/894
st.markdown("""
<style>
    button.step-up {display: none;}
    button.step-down {display: none;}
    div[data-baseweb] {border-radius: 4px;}
</style>""",
unsafe_allow_html=True)


#st.markdown("# Netrisk-serve")
#st.markdown("### Station management, trace view, and data download")

stat_and_traces = st.Page("pages/10_Stations_and_traces.py", title="Stations and traces", icon="📌")
add_xml = st.Page("pages/20_Add_station_XML.py", title="Create new", icon="✏️")
list_xml = st.Page("pages/21_List_station_XML.py", title="Manage files", icon="✏️")
ftp_accounts = st.Page("pages/30_Add_station_FTP_account.py", title="Create new", icon="✏️")

pg = st.navigation(
        {
            "Stations and Traces": [stat_and_traces],
            "Station XML files": [add_xml, list_xml],
            "FTP accounts": [ftp_accounts],
        }
    )
pg.run()

# former page config handling

## st.page_link("Home.py", label="Home", icon="🏠")
#st.page_link("pages/10_Stations_and_traces.py", label="Stations", icon="📌")
#st.page_link("pages/20_Add_station_XML.py", label="StationXML", icon="📈")
#st.page_link("pages/21_List_station_XML.py", label="StationXML", icon="📈")
#st.page_link("pages/30_Add_station_FTP_account.py", label="StationFTP")
#st.page_link("http://seiscomp:8080", label="FDSN Web Service", icon="➡️")
