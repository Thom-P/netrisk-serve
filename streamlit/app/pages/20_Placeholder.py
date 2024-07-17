import os
import string

import streamlit as st
from obspy import UTCDateTime
from obspy.clients.nrl import NRL
from obspy.core.inventory import Inventory, Network, Station, Channel, Site


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
code_help_str = "1 - 8 uppercase alphanumeric or dash characters"
coord_help_str = "in decimal degrees - WGS84"

net_url = 'http://docs.fdsn.org/projects/source-identifiers/en/v1.0/network-codes.html#'
st.page_link(net_url, label=':blue[More info on naming conventions ↗]')

cols1 = st.columns(6)
net_code = cols1[0].text_input("__Network code__", value="", max_chars=8, type="default", help=code_help_str, placeholder="")
sta_code = cols1[1].text_input("__Station code__", value="", max_chars=8, type="default", help=code_help_str, placeholder="")
lat = cols1[2].number_input("__Station latitude__", value=44.3387, min_value=-90.0, max_value=90.0, format="%.4f", help=coord_help_str) 
lon = cols1[3].number_input("__Station longitude__", value=1.2097, min_value=-180.0, max_value=180.0, format="%.4f", help=coord_help_str) 
elev = cols1[4].number_input("__Ground surface elevation__ (m)", value=0, min_value=-414, max_value=8848, format="%d")
site = cols1[5].text_input("__Station site name__", value="", max_chars=64, type="default", help=None) 


def is_valid_code(code, valid_chars):
    # Following norm: http://docs.fdsn.org/projects/source-identifiers/en/v1.0/definition.html
    if len(code) < 1 or len(code) > 8:
        return False
    if any(c not in valid_chars for c in code):
        return False
    return True

if net_code is None or is_valid_code(net_code, valid_chars) is False:
    #st.write(":red[Invalid or empty network code!]")
    st.warning('Invalid or empty network code', icon="⚠️")
    st.stop()
elif sta_code is None or is_valid_code(sta_code, valid_chars) is False:
    #st.write(":red[Invalid or empty station code!]")
    st.warning('Invalid or empty station code', icon="⚠️")
    st.stop()

sta = Station(
        code=sta_code,
        latitude=lat,
        longitude=lon,
        elevation=elev,
        site=Site(name=site)
)

net = Network(
        code=net_code,
        stations=[sta],
)

st.success(f"{sta}", icon="✅")

st.divider()
############################################################################
st.markdown("## Channel(s)")

st.markdown("### Channel code(s)")

band_url = 'http://docs.fdsn.org/projects/source-identifiers/en/v1.0/channel-codes.html#band-code'
st.page_link(band_url, label=':blue[More info on channel codes ↗]')

band_codes = {
    'J': 'fs > 5000', 
    'F': '1000 ≤ fs < 5000, Tc ≥ 10',
    'G': '1000 ≤ fs < 5000, Tc < 10', 
    'D': '250 ≤ fs < 1000, Tc < 10',
    'C': '250 ≤ fs < 1000, Tc ≥ 10', 
    'E': 'Extremely Short Period, 80 ≤ fs < 250, Tc < 10',
    'S': 'Short Period, 10 ≤ fs < 80, Tc < 10',
    'H': 'High Broadband, 80 ≤ fs < 250, Tc ≥ 10',
    'B': 'Broadband, 10 ≤ fs < 80, Tc ≥ 10',
    'M': 'Mid Period, 1 < fs < 10',
    'L': 'Long Period, fs ~ 1',
    'V': 'Very Long Period, 0.1 ≤ fs < 1',
    'U': 'Ultra Long Period, 0.01 ≤ fs < 0.1', 
    'W': 'Ultra-ultra Long Period, 0.001 ≤ fs < 0.01', 
    'R': 'Extremely Long Period, 0.0001 ≤ fs < 0.001',
    'P': 'On the order of 0.1 to 1 day, 0.00001 ≤ fs < 0.0001',
    'T': 'On the order of 1 to 10 days, 0.000001 ≤ fs < 0.00001',
    'Q': 'Greater than 10 days, fs < 0.000001',
    'I': 'Irregularly sampled'
}

cols2 = st.columns(3)
band_code = cols2[0].selectbox("__Band code__ - fs: sample rate (Hz); Tc: lower period bound of instrument response (s)", band_codes, format_func=lambda code: f'{code} - {band_codes[code]}')
if band_code is None:
    st.stop()

source_codes = {
    'H': 'High Gain Seismometer',
    'L': 'Low Gain Seismometer',
    'M': 'Mass Position Seismometer',
    'N': 'Accelerometer',
    'P': 'Geophone, very short period seismometer with natural frequency 5 - 10 Hz or higher',
    'A': 'Tilt Meter',
    'B': 'Creep Meter',
    'C': 'Calibration input',
    'D': 'Pressure',
    'E': 'Electronic Test Point',
    'F': 'Magnetometer',
    'I': 'Humidity',
    'J': 'Rotational Sensor',
    'K': 'Temperature',
    'O': 'Water Current',
    'G': 'Gravimeter',
    'Q': 'Electric Potential',
    'R': 'Rainfall',
    'S': 'Linear Strain',
    'T': 'Tide',
    'U': 'Bolometer',
    'V': 'Volumetric Strain',
    'W': 'Wind',
    'X': 'Derived or generated channel',
    'Y': 'Non-specific instruments',
    'Z': 'Synthesized Beams'
}

source_code = cols2[1].selectbox("__Source code (instrument)__", source_codes, format_func=lambda code: f'{code} - {source_codes[code]}')
if band_code is None:
    st.stop()

# need one category per source code...todo
subsource_codes = { 
    'N, E, Z': 'North, East, Up',
    '1, 2, Z': 'Orthogonal components, nontraditional horizontals',
    '1, 2, 3': 'Orthogonal components, nontraditional orientations',
    'T, R': 'For rotated components or beams (Transverse, Radial)',
    'A, B, C': 'Triaxial (Along the edges of a cube turned up on a corner)',
    'U, V, W': 'Optional components, also used for raw triaxial output',
    'N': 'North',
    'E': 'East',
    'Z': 'Up',
    '1': 'Orthogonal components, nontraditional orientations',
    '2': 'Orthogonal components, nontraditional orientations',
    '3': 'Orthogonal components, nontraditional orientations',
    'T': 'For rotated components or beams (Transverse)',
    'R': 'For rotated components or beams (Radial)',
}

subsource_code = cols2[2].selectbox("__Subsource code(s) (components)__", subsource_codes, format_func=lambda code: f'{code} - {subsource_codes[code]}')
if subsource_code is None:
    st.stop()
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
def create_xml():
    fname = f'{net}.{stat}.xml'
    inv.write(f'/data/inventory/ {fname}', format="stationxml", validate=True)
    return

# todo: warn override if file exists (or same net code, stat exists)
st.button("Create station XML", on_click=create_xml, type="secondary")