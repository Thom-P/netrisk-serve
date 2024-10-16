import os
import io

import streamlit as st
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
from obspy import UTCDateTime
from obspy.clients.nrl import NRL
from obspy.core.inventory import Inventory, Network, Station, Channel, Site
from obspy.core.inventory.util import Equipment
import pandas as pd

from utils.XML_build import get_station_parameters, build_station_and_network_objects, get_channel_codes, choose_device, build_channel_objects, get_channel_start_stop, add_channels_without_duplicates


#st.title('Add station')
st.header('Create station XML')

# Instrument and responses online catalog
# todo deprecated: need to use v2 offline copy instead...
nrl = NRL() # tmp revert to online
#nrl = NRL('./NRL')


if 'saved_channels' not in st.session_state:
    st.session_state.saved_channels = []

############################################################################
st.subheader("Station parameters")

net_code, sta_code, lat, lon, elev, site = get_station_parameters()

net, sta = build_station_and_network_objects(net_code, sta_code, lat, lon, elev, site)  #
st.success(f"__Station__: {net.code}.{sta.code} ({sta.site.name}) — __Latitude, Longitude__: {sta.latitude:.4f}, {sta.longitude:.4f} — __Elevation__: {sta.elevation} m", icon="✅")
st.divider()

############################################################################
st.subheader("Channel code(s)")
channels = []

band_url = 'http://docs.fdsn.org/projects/source-identifiers/en/v1.0/channel-codes.html#band-code'
st.page_link(band_url, label=':blue[More info on channel codes ↗]')
use_old_format = st.toggle("Use SEED v2.4 deprecated format for channel code (eg: HHZ)", value = True, disabled=True, help="Seiscomp FDSNWS does not seem to handle newer format, older format enforced for the moment.")
band_code, source_code, subsource_code = get_channel_codes()
start_datetime, end_datetime = get_channel_start_stop()

# todo: add response params to session_state?
response = None
sensor = None
datalogger = None
attach_response = st.toggle("Choose sensor and digitizer to include instrument response", value = False)
if attach_response:
    sensor_keys = choose_device(nrl.sensors, 'Sensor')
    sensor = Equipment(manufacturer=sensor_keys[0], type=sensor_keys[1], description='; '.join(sensor_keys[2:]))
    datalogger_keys = choose_device(nrl.dataloggers, 'Datalogger')
    datalogger = Equipment(manufacturer=datalogger_keys[0], type=datalogger_keys[1], description='; '.join(datalogger_keys[2:]))
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
curr_channels = build_channel_objects(band_code, source_code, subsource_code, use_old_format, start_datetime, end_datetime, response, sensor, datalogger, sta, placeholder)

if st.button("Add channel(s)", type='primary'):
    #st.session_state.saved_channels.extend(curr_channels)  # add to onclick callback instead
    add_channels_without_duplicates(curr_channels)

    #for chan in curr_channels:
    #    st.toast(f"Channel(s) {chan.code} added successfully", icon=None)
    #placeholder.empty()
    # keep curr resp inst/dl in seesion state

st.divider()
#######################################
## Display channels
st.subheader("Summary")
#st.write("__Station:__")
st.markdown("#### Station:")
#st.write(f"{net.code}.{sta.code} ({sta.site.name}) — Latitude, Longitude = {sta.latitude}, {sta.longitude} — Elevation = {sta.elevation} m")
st.info(f"__Code__: {net.code}.{sta.code} ({sta.site.name}) — __Latitude, Longitude__: {sta.latitude:.4f}, {sta.longitude:.4f} — __Elevation__: {sta.elevation} m")

#st.write("__Channels:__")
st.markdown("#### Channels:")
channels_data =[]
for i, cha in enumerate(st.session_state.saved_channels):
    #chan_info = f"{cha.code}, loc:{cha.location_code}, lat: {cha.latitude}, lon: {cha.longitude}, elev: {cha.elevation}, depth: {cha.depth}, sens=, l="
    if cha.response is not None:
        sensor = cha.equipments[0]
        datalogger = cha.equipments[1]
        sensor_str = f"{sensor.manufacturer} - {sensor.type} ({sensor.description})"
        datalogger_str = f"{datalogger.manufacturer} - {datalogger.type} ({datalogger.description})"
    else:
        sensor_str = "None"
        datalogger_str = "None"

    channels_data.append((cha.code, cha.location_code, cha.start_date, cha.end_date, cha.latitude, cha.longitude, cha.elevation, cha.depth, sensor_str, datalogger_str))
    #st.write(chan_info)
df = pd.DataFrame(channels_data, columns=['Channel code', 'Location code', 'Start date (UTC)', 'End date (UTC)', 'Latitude (°)', 'Longitude (°)', 'Elevation (m)', 'Depth (m)', 'Sensor', 'Datalogger'])
event = st.dataframe(df, hide_index=True, on_select='rerun',
    column_config={
        'Latitude (°)': st.column_config.NumberColumn(format="%.4f"),
        'Longitude (°)': st.column_config.NumberColumn(format="%.4f"),
        'Start date (UTC)': st.column_config.DatetimeColumn(
                    format="DD MMM YYYY, HH:mm",
                    step=60,
                ),
        'End date (UTC)': st.column_config.DatetimeColumn(
                    format="DD MMM YYYY, HH:mm",
                    step=60,
                ),
    })


def delete_rows(rows):
    for row in reversed(rows):  # reverse so that delete doesnt change remaining indices
        del st.session_state.saved_channels[row]

selected_rows = event.selection['rows']
if len(selected_rows) > 0 and st.button("Delete selected rows", on_click=delete_rows, args=[selected_rows]):
    pass

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

#fpath = '/data/inventory/'
fpath = '/data/xml/'
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
    if 'stations_txt' in st.session_state:
        del st.session_state['stations_txt']  # to allow update
    if 'df_stations' in st.session_state:
        del st.session_state['df_stations']
    del st.session_state['saved_channels'] # to prevent mess
