import streamlit as st
from st_pages import show_pages, Page, Section, add_page_title

# st-pages: third-party package to add page subsections
#add_page_title('test')
show_pages(
    [
        Page("pages/10_Stations_and_traces.py", "Stations and traces", "📌"),
        # Can use :<icon-name>: or the actual icon
        # Since this is a Section, all the pages underneath it will be indented
        # The section itself will look like a normal page, but it won't be clickable
        Section(name="Station XML files", icon="📖"),
        Page("pages/20_Add_station_XML.py", "Create new", "✏️"),
        # The pages appear in the order you pass them
        Page("pages/21_List_station_XML.py", "Manage files", "✏️"),
        Section(name="Station FTP accounts", icon="📖"),
        Page("pages/30_Add_station_FTP_account.py", "Create new", "✏️"),
        # You can also pass in_section=False to a page to make it un-indented
        #Page("example_app/example_five.py", "Example Five", "🧰", in_section=False),
    ]
)




# former page config handling
#st.set_page_config(
#    page_title='Home',
#    page_icon=None,
#    layout="wide",
#    initial_sidebar_state="auto",
#    menu_items=None
#)
# st.sidebar.markdown("# Home")

sidebar_logo = "static/netrisk-serve-hr-logo-transparent.png"
main_body_logo = "static/netrisk-serve-icon-transparent.png"
st.logo(sidebar_logo, icon_image=main_body_logo)

st.markdown("# Netrisk-serve")
st.markdown("### Station management, trace view, and data download")


# st.page_link("Home.py", label="Home", icon="🏠")
st.page_link("pages/10_Stations_and_traces.py", label="Stations", icon="📌")
st.page_link("pages/20_Add_station_XML.py", label="StationXML", icon="📈")
st.page_link("pages/21_List_station_XML.py", label="StationXML", icon="📈")
st.page_link("pages/30_Add_station_FTP_account.py", label="StationFTP")
st.page_link("http://seiscomp:8080", label="FDSN Web Service", icon="➡️")
