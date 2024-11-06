import os
import io

import streamlit as st
from obspy.clients.nrl import NRL
from obspy.core.inventory import Inventory
from obspy.core.inventory.util import Equipment
import pandas as pd

from utils.XML_build import (
    get_station_parameters, build_station_and_network_objects,
    get_channel_codes, choose_device, build_channel_objects,
    get_channel_start_stop, add_channels_without_duplicates,
    fetch_resp_units, build_custom_geophone_response,
    build_custom_datalogger_response
)
from utils.dataframe import dataframe_with_selections


st.header('Create station XML')

# Instrument and responses online catalog
# todo deprecated: need to use v2 offline copy instead...
# If using v2, need to rethink custom geophone response creation?
nrl = NRL()  # tmp revert to online
# nrl = NRL('./NRL')


if 'saved_channels' not in st.session_state:
    st.session_state.saved_channels = []

############################################################################
st.subheader("Station parameters")

net_code, sta_code, lat, lon, elev, site = get_station_parameters()

net, sta = build_station_and_network_objects(
    net_code, sta_code, lat, lon, elev, site
)
st.success(
    f"__Station__: {net.code}.{sta.code} ({sta.site.name}) — "
    f"__Latitude, Longitude__: {sta.latitude:.4f}, "
    f"{sta.longitude:.4f} — __Elevation__: {sta.elevation} m",
    icon="✅"
)
st.divider()

############################################################################
st.subheader("Channel code(s)")
channels = []

band_url = ('http://docs.fdsn.org/projects/source-identifiers/en/v1.0'
            '/channel-codes.html#band-code')
st.page_link(band_url, label=':blue[More info on channel codes ↗]')
use_old_format = st.toggle(
    "Use SEED v2.4 deprecated format for channel code (eg: HHZ)",
    value=True, disabled=True,
    help=("Seiscomp FDSNWS does not seem to handle newer format, "
          "older format enforced for the moment.")
)
band_code, source_code, subsource_code = get_channel_codes()
start_datetime, end_datetime = get_channel_start_stop()

# todo: add response params to session_state?
response = None
sensor = None
sensor_resp = None
datalogger = None
attach_response = st.radio(
    "Do you want to include the instrument response?",
    ("Yes", "No"), horizontal=True, index=None
)
if attach_response is None:
    st.stop()
if attach_response == "Yes":
    st.markdown("### Sensor")
    sensor_type = st.radio(
        "",
        ("Choose from the IRIS Nominal Response Library",
         "Create a custom geophone"),
        index=None,
        label_visibility="collapsed"
    )
    if sensor_type is None:
        st.stop()
    is_custom_sensor = sensor_type == "Create a custom geophone"
    if is_custom_sensor:
        sensor_resp, description = build_custom_geophone_response()
        sensor = Equipment(
            manufacturer='Unknown/Custom', type='Geophone',
            description=description
        )
    else:
        sensor_keys = choose_device(nrl.sensors)
        sensor = Equipment(
            manufacturer=sensor_keys[0], type=sensor_keys[1],
            description='; '.join(sensor_keys[2:])
        )
        sensor_resp, _ = nrl._get_response("sensors", keys=sensor_keys)

    st.markdown("### Datalogger")
    datalogger_type = st.radio(
        "",
        ("Choose from the IRIS Nominal Response Library",
         "Create a custom datalogger"),
        index=None, label_visibility="collapsed"
    )
    if datalogger_type is None:
        st.stop()
    is_custom_datalogger = datalogger_type == "Create a custom datalogger"
    if is_custom_datalogger:
        datalogger_resp, description = build_custom_datalogger_response()
        datalogger = Equipment(
            manufacturer='Unknown/Custom', type='Datalogger',
            description=description
        )
    else:
        datalogger_keys = choose_device(nrl.dataloggers)
        datalogger = Equipment(
            manufacturer=datalogger_keys[0], type=datalogger_keys[1],
            description='; '.join(datalogger_keys[2:])
        )
        datalogger_resp, _ = nrl._get_response(
            "dataloggers", keys=datalogger_keys
        )
    with st.spinner('Loading response file...'):
        response = nrl._combine_sensor_datalogger(
            sensor_resp, datalogger_resp, '', ''
        )

    with st.expander("Visualize instrument response"):
        # st.info(response, icon="ℹ️") # messes format
        cols = st.columns(2, vertical_alignment="center")
        with cols[0]:
            st.write(response)
        # fig, (ax0, ax1) = plt.subplots(2, 1)
        # response.plot(1e-3, axes=(ax0, ax1))
        with cols[1]:
            with st.spinner('Loading plot...'):
                plot_buffer = io.BytesIO()
                fig = response.plot(1e-3, output='DEF', show=False)
                unit_str = fetch_resp_units(response)
                fig.axes[0].set_ylabel(f'Amplitude [{unit_str}]')
                fig.savefig(plot_buffer)
                st.image(plot_buffer, use_column_width=True)

placeholder = st.empty()  # for cleaning widgets
curr_channels = build_channel_objects(
    band_code, source_code, subsource_code, use_old_format,
    start_datetime, end_datetime, response, sensor, datalogger,
    sta, placeholder
)

if st.button("Add channel(s)", type='primary'):
    add_channels_without_duplicates(curr_channels)
    # for chan in curr_channels:
    #    st.toast(f"Channel(s) {chan.code} added successfully", icon=None)
    # placeholder.empty()
    # keep curr resp inst/dl in seesion state

st.divider()
#######################################
# Display channels
st.subheader("Summary")
st.markdown("#### Station:")
st.info(f"__Code__: {net.code}.{sta.code} ({sta.site.name}) — __Latitude, "
        f"Longitude__: {sta.latitude:.4f}, {sta.longitude:.4f} — "
        f"__Elevation__: {sta.elevation} m")
st.markdown("#### Channels:")
channels_data = []
for i, cha in enumerate(st.session_state.saved_channels):
    # chan_info = f"{cha.code}, loc:{cha.location_code}, lat: {cha.latitude},
    # lon: {cha.longitude}, elev: {cha.elevation}, depth: {cha.depth}, sens=,
    # l="
    if cha.response is not None:
        sensor = cha.equipments[0]
        datalogger = cha.equipments[1]
        sensor_str = (f"{sensor.manufacturer} - {sensor.type} "
                      f"({sensor.description})")
        datalogger_str = (f"{datalogger.manufacturer} - {datalogger.type} "
                          f"({datalogger.description})")
    else:
        sensor_str = "None"
        datalogger_str = "None"

    channels_data.append(
        (cha.code, cha.location_code, cha.start_date, cha.end_date,
         cha.latitude, cha.longitude, cha.elevation, cha.depth,
         sensor_str, datalogger_str)
    )
    # st.write(chan_info)
df = pd.DataFrame(
    channels_data,
    columns=[
        'Channel code', 'Location code', 'Start date (UTC)', 'End date (UTC)',
        'Latitude (°)', 'Longitude (°)', 'Elevation (m)', 'Depth (m)',
        'Sensor', 'Datalogger'
    ]
)
# event = st.dataframe(df, hide_index=True, on_select='rerun',
selection = dataframe_with_selections(
    df,
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
    }
)


def delete_rows(rows):
    # reverse so that delete doesnt change remaining indices
    for row in reversed(rows):
        del st.session_state.saved_channels[row]


selected_rows = selection['selected_rows']
selected_rows_indices = selection['selected_rows_indices']
is_disabled = len(selected_rows) == 0
if st.button("Delete selected row(s)", disabled=is_disabled,
             on_click=delete_rows, args=selected_rows_indices):
    pass

############################
# XML File creation

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


fpath = '/data/xml/'
fname = f"{fpath}{net_code}.{sta_code}.xml"
if os.path.isfile(fname):
    st.warning(f"{net_code}.{sta_code}.xml already exists on the server!",
               icon="⚠️")
    create_button_msg = f"Overwrite {net_code}.{sta_code}.xml  station XML"
else:
    create_button_msg = f"Create {net_code}.{sta_code}.xml"

create = st.button(create_button_msg, type="primary")
if create:
    if len(st.session_state.saved_channels) == 0:
        st.error("You need at least one channel to create a station xml file!",
                 icon="🚨")
        st.stop()
    res = create_xml(fname, net)
    st.success("StationXML file created successfully", icon="✅")
    if 'stations_txt' in st.session_state:
        del st.session_state['stations_txt']  # to allow update
    if 'df_stations' in st.session_state:
        del st.session_state['df_stations']
    del st.session_state['saved_channels']  # to prevent mess
