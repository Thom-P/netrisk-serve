import os
import io

import streamlit as st
import streamlit.components.v1 as components
import mpld3
import matplotlib.pyplot as plt
from obspy import UTCDateTime
from obspy.clients.nrl import NRL
from obspy.core.inventory import Inventory, Network, Station, Channel, Site

from utils.XML_build import get_station_parameters, is_valid_code, build_station_and_network_objects, get_channel_codes, choose_device, build_channel_objects

st.set_page_config(
    page_title='Add station',
    page_icon=None,
    layout="wide",
    initial_sidebar_state="auto",
    menu_items=None
)
# st.sidebar.markdown('# Placeholder')

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

st.title('Add station')

# Instrument and responses online catalog
# todo deprecated: need to use v2 offline copy instead...
nrl = NRL()

if 'saved_channels' not in st.session_state:
    st.session_state.saved_channels = []
 
############################################################################
st.markdown("## Station parameters")

net_code, sta_code, lat, lon, elev, site = get_station_parameters()

net, sta = build_station_and_network_objects(net_code, sta_code, lat, lon, elev, site)
st.success(f"Station {net.code}.{sta.code} ({sta.site.name}) — Latitude, Longitude = {sta.latitude}, {sta.longitude} — Elevation = {sta.elevation} m", icon="✅")
st.divider()

############################################################################
st.markdown("## Instrument(s)")
#myInstruments = []
#if st.button

channels = []
st.markdown("### Channel code(s)")

band_url = 'http://docs.fdsn.org/projects/source-identifiers/en/v1.0/channel-codes.html#band-code'
st.page_link(band_url, label=':blue[More info on channel codes ↗]')
band_code, source_code, subsource_code = get_channel_codes()

response = None
attach_response = st.toggle("Choose sensor and digitizer to include instrument response", value = False)
if attach_response:
    sensor_keys = choose_device(nrl.sensors, 'Sensor')
    datalogger_keys = choose_device(nrl.dataloggers, 'Datalogger')
    with st.spinner('Loading response file...'):
        response = nrl.get_response(
            sensor_keys=sensor_keys,
            datalogger_keys=datalogger_keys
        )
    with st.expander("Visualize instrument response"):
        #st.info(response, icon="ℹ️") # messes format
        cols = st.columns(2, vertical_alignment="center")
        with cols[0]:
            st.write(response)
        #fig, (ax0, ax1) = plt.subplots(2, 1)
        #response.plot(1e-3, axes=(ax0, ax1))
        with cols[1]:
            with st.spinner('Loading plot...'):
                plot_buffer = io.BytesIO()
                response.plot(1e-3, outfile=plot_buffer)
                st.image(plot_buffer, use_column_width=True)

placeholder = st.empty() # for cleaning widgets
curr_channels = build_channel_objects(band_code, source_code, subsource_code, response, sta, placeholder)
#st.session_state.current_channels = curr_channels
st.session_state
if st.button("Add channel(s)", type='primary'):
    st.session_state.saved_channels.extend(curr_channels)  # add to onclick callback instead
    # could add here a way to prevent double channels
    for chan in curr_channels:
        st.toast(f"Channel(s) {chan.code} added successfully", icon=None)
    placeholder.empty()
    #st.session_state.current_channels = []
    # how to remove chan widgets?
    # keep curr resp inst/dl in seesion state

st.session_state
#channels.append(curr_channels)

st.divider()
#######################################
## Display channels
st.markdown("### Summary")
st.write("Station:")
st.write(f"{net.code}.{sta.code} ({sta.site.name}) — Latitude, Longitude = {sta.latitude}, {sta.longitude} — Elevation = {sta.elevation} m")

st.write("Channels:")
st.write(len(st.session_state.saved_channels))
for i, cha in enumerate(st.session_state.saved_channels):
    chan_info = f"{cha.code}, loc:{cha.location_code}, lat: {cha.latitude}, lon: {cha.longitude}, elev: {cha.elevation}, depth: {cha.depth}, sens=, l="
    st.write(chan_info)

############################ 
## XML File creation

# Write to a StationXML file. Also force a validation against
# the StationXML schema to ensure it produces a valid StationXML file.
def create_xml(fname, net):
    net.stations[0].channels = st.session_state.saved_channels
    inv = Inventory(
        networks=[net],
        source=os.environ["UI_USER"]  # todo add institution
    )
    st.write(inv)
    res = inv.write(fname, format="stationxml", validate=True)
    return res

fpath = '/data/inventory/'
fname = f"{fpath}{net_code}.{sta_code}.xml"
if os.path.isfile(fname):
    st.warning(f"{net_code}.{sta_code}.xml already exists on the server!", icon="⚠️")
    create_button_msg = f"Overwrite {net_code}.{sta_code}.xml  station XML"
else:
    create_button_msg = f"Create {net_code}.{sta_code}.xml"

create = st.button(create_button_msg, type="primary")
if create:
    if len(st.session_state.saved_channels) == 0:
        st.error("You need at least one channel to create a station xml file!", icon="🚨")
        st.stop()
    res = create_xml(fname, net)
    st.success("StationXML file created successfully", icon="✅")


   #with st.form("new_station_form"):
#    checkbox_val = st.checkbox("Form checkbox")

#    # Every form must have a submit button.
#    submitted = st.form_submit_button("Submit")
#    if submitted:
#        st.write("net", net, "checkbox", checkbox_val)

#st.write("Outside the form")
