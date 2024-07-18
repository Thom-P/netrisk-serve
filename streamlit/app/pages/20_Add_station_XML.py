import os
import string

import streamlit as st
from obspy import UTCDateTime
from obspy.clients.nrl import NRL
from obspy.core.inventory import Inventory, Network, Station, Channel, Site

from utils.XML_build import get_station_parameters, is_valid_code, build_station_and_network_objects, get_channel_codes

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

############################################################################
st.markdown("## Station parameters")

valid_chars = set(string.ascii_uppercase + string.digits + '-')
net_code, sta_code, lat, lon, elev, site = get_station_parameters()

if net_code is None or is_valid_code(net_code, valid_chars) is False:
    st.warning('Invalid or empty network code', icon="⚠️")
    st.stop()
elif sta_code is None or is_valid_code(sta_code, valid_chars) is False:
    st.warning('Invalid or empty station code', icon="⚠️")
    st.stop()
elif len(site) == 0: 
    st.warning('Empty site name', icon="⚠️")
    st.stop()

net, sta = build_station_and_network_objects(net_code, sta_code, lat, lon, elev, site)
st.success(f"Station {net.code}.{sta.code} ({sta.site.name}) - Lat., Lon. = {sta.latitude}, {sta.longitude} - Elev. = {sta.elevation} m", icon="✅")
st.divider()

############################################################################
st.markdown("## Channel(s)")

st.markdown("### Channel code(s)")

band_url = 'http://docs.fdsn.org/projects/source-identifiers/en/v1.0/channel-codes.html#band-code'
st.page_link(band_url, label=':blue[More info on channel codes ↗]')
band_code, source_code, subsource_code = get_channel_codes()
subsource_code_list = subsource_code.split(', ')

# todo make it optional
## Sensor choice
def create_selectbox(choices: dict, col):
    label = choices.__str__().partition('(')[0]
    choice = col.selectbox(label, choices.keys(), index=None, placeholder="Choose an option")
    return choice

# todo make sure max depth is not greater than 6
st.markdown("### Sensor")
col_sensor = st.columns(6, vertical_alignment="bottom")
i_col = 0
sensor_keys=[]
curr_choices = nrl.sensors
while isinstance(curr_choices, dict):
    col = col_sensor[i_col]
    choice = create_selectbox(curr_choices, col)
    i_col += 1
    if choice is None:
        st.stop()
    else:
        sensor_keys.append(choice)
        curr_choices = curr_choices[choice]
curr_choices

#st.divider()

# todo make sure max depth is not greater than 6
st.markdown("### Datalogger")
col_datalogger = st.columns(6, vertical_alignment="bottom")
j_col = 0
datalogger_keys=[]
curr_choices = nrl.dataloggers
while isinstance(curr_choices, dict):
    col = col_datalogger[j_col]
    choice = create_selectbox(curr_choices, col)
    j_col += 1
    if choice is None:
        st.stop()
    else:
        datalogger_keys.append(choice)
        curr_choices = curr_choices[choice]
curr_choices

with st.spinner('Loading response file...'):
    response = nrl.get_response(
        sensor_keys=sensor_keys,
        datalogger_keys=datalogger_keys
    )
    response

#######################################
## Display channels

col3 = st.columns(len(subsource_code_list))
channels = []
for i, sub_code in enumerate(subsource_code_list):
    cont = col3[i].container(border=True)
    chan_code = '_'.join((band_code, source_code, sub_code))
    with cont:
        st.write(f"__Channel {chan_code}__")
        loc_code = st.text_input("Location code", value="00", max_chars=8, type="default", help=code_help_str, key=f'loc{band_code}{source_code}{sub_code}')
        chan_lat = st.number_input("__Channel latitude__", value=lat, min_value=-90.0, max_value=90.0, format="%.4f", help=coord_help_str, key=f'lat{band_code}{source_code}{sub_code}') 
        chan_lon = st.number_input("__Channel longitude__", value=lon, min_value=-180.0, max_value=180.0, format="%.4f", help=coord_help_str, key=f'lon{band_code}{source_code}{sub_code}') 
        chan_depth = st.number_input("__Sensor depth__ (m)", value=0, min_value=-1000, max_value=10000, format="%d", help="Positive value for buried sensors", key=f'depth{band_code}{source_code}{sub_code}')
        chan_elev = elev - chan_depth
        st.write(f"__Sensor elevation__ = {chan_elev} m") 
        #st.number_input("__Sensor elevation__ (m)", value=elev, min_value=-10000, max_value=10000, format="%d", help="Should correspond to ground elevation minus depth", key=f'elev{band_code}{source_code}{sub_code}')
    cha = Channel(
        code=chan_code,
        location_code=loc_code,
        # Note that these coordinates can differ from the station coordinates.
        latitude=chan_lat,
        longitude=chan_lon,
        elevation=chan_elev,
        depth=chan_depth,
        #azimuth=0.0,
        #dip=-90.0,
        #sample_rate=200
    )
    channels.append(cha)

# make add chans tab, start and end time, chan code, and the sens, digit, 

st.divider()

## Summary
st.markdown("Summary")

#with st.form("new_station_form"):
#    checkbox_val = st.checkbox("Form checkbox")

#    # Every form must have a submit button.
#    submitted = st.form_submit_button("Submit")
#    if submitted:
#        st.write("net", net, "checkbox", checkbox_val)

#st.write("Outside the form")

def create_inv(net, sta, channels, response):
# Inventory template for writing stationXML file
    inv = Inventory(
        networks=[net],
        source=os.environ["UI_USER"]
    )
    
    # Now tie it all together.
    #[cha.response = response for cha in channels]
    for cha in channels:
        cha.response = response
    sta.channels = channels
    return inv

inv = create_inv(net, sta, channels, response)
st.write(inv)

# Write to a StationXML file. Also force a validation against
# the StationXML schema to ensure it produces a valid StationXML file.
def create_xml(fname):
    res = inv.write(fname, format="stationxml", validate=True)
    return res

fpath = '/data/inventory/'
fname = f"{fpath}{net_code}.{sta_code}.xml"
if os.path.isfile(fname):
    st.warning(f"{net_code}.{sta_code}.xml already exists on the server!", icon="⚠️")
    create_button_msg = 'Overwrite existing station XML'
else:
    create_button_msg = 'Create station XML'

# todo: warn override if file exists (or same net code, stat exists)
create = st.button(create_button_msg, type="secondary")
if create:
    res = create_xml(fname)
    st.success("StationXML file created successfully", icon="✅")
