import os
import string

import streamlit as st
from obspy import UTCDateTime
from obspy.clients.nrl import NRL
from obspy.core.inventory import Inventory, Network, Station, Channel, Site


st.set_page_config(
    page_title='Add stations',
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

st.title('Add stations')

# Instrument and responses online catalog
# todoldeprecated: need to use v2 offline copy instead...
# todo: verify sensor and datalogger keys "depth"
nrl = NRL()

############################################################################
st.markdown("## Station parameters")

# todo: add validation for all inputs, min num of chars, type of chars, etc
cols1 = st.columns(7)

valid_chars = set(string.ascii_uppercase + string.digits + '-')
code_help_str = "1 - 8 uppercase alphanumeric or dash characters"
coord_help_str = "in decimal degrees - WGS84"
net_code = cols1[0].text_input("Network code", value="", max_chars=8, type="default", help=code_help_str, placeholder="")
sta_code = cols1[1].text_input("Station code", value="", max_chars=8, type="default", help=code_help_str, placeholder="")
lat = cols1[2].number_input("Station latitude", value=44.3387, min_value=-90.0, max_value=90.0, format="%.4f", help=coord_help_str) 
lon = cols1[3].number_input("Station longitude", value=1.2097, min_value=-180.0, max_value=180.0, format="%.4f", help=coord_help_str) 
elev = cols1[4].number_input("Ground surface elevation (m)", value=0, min_value=-414, max_value=8848, format="%d")
site = cols1[5].text_input("Station site name", value="", max_chars=64, type="default", help=None) 


def is_valid_code(code, valid_chars):
    # Following norm: http://docs.fdsn.org/projects/source-identifiers/en/v1.0/definition.html
    if len(code) < 1 or len(code) > 8:
        return False
    if any(c not in valid_chars for c in code):
        return False
    return True

if net_code is None or is_valid_code(net_code, valid_chars) is False or sta_code is None or is_valid_code(sta_code, valid_chars) is False:
    st.write("Incomplete or invalid field...")
    st.stop()
else:
    st.write((net_code, sta_code, lat, lon, elev, site))

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

############################################################################
st.markdown("## Channels")
band_url = 'http://docs.fdsn.org/projects/source-identifiers/en/v1.0/channel-codes.html#band-code'
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
st.page_link(band_url, label=':blue[More info on band codes ↗]')
band_code = st.selectbox("Band code (fs: sample rate, Tc: lower bound of instrument response)", band_codes, format_func=lambda code: f'{code}: {band_codes[code]}')
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

source_url = 'http://docs.fdsn.org/projects/source-identifiers/en/v1.0/channel-codes.html#source-and-subsource-codes'
st.page_link(source_url, label=':blue[More info on source codes? ↗]')
source_code = st.selectbox("Source code", source_codes, format_func=lambda code: f'{code}: {source_codes[code]}')
if band_code is None:
    st.stop()
band_code, source_code

chan = st.text_input("Channel code", value="", max_chars=3, type="default", help=None)
#cols1 = st.columns(7)
loc_code = st.text_input("Location code", value="", max_chars=8, type="default", help=code_help_str, placeholder="")
chan, loc_code
#make location num instead, add lat lon dep az dip
# make add chans tab, start and end time, chan code, and the sens, digit, 

def create_selectbox(choices: dict):
    label = choices.__str__().partition('(')[0]
    choice = st.selectbox(label, choices.keys(), index=None, placeholder="Choose an option")
    return choice

st.markdown("## Sensor")
sensor_keys=[]
curr_choices = nrl.sensors
while isinstance(curr_choices, dict):
    choice = create_selectbox(curr_choices)
    if choice is None:
        st.stop()
    else:
        sensor_keys.append(choice)
        curr_choices = curr_choices[choice]
curr_choices

st.markdown("## Datalogger")
datalogger_keys=[]
curr_choices = nrl.dataloggers
while isinstance(curr_choices, dict):
    choice = create_selectbox(curr_choices)
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

#with st.form("new_station_form"):
#    checkbox_val = st.checkbox("Form checkbox")

#    # Every form must have a submit button.
#    submitted = st.form_submit_button("Submit")
#    if submitted:
#        st.write("net", net, "checkbox", checkbox_val)

#st.write("Outside the form")

def create_inv(net, sta, lat, lon, elev, site, chan, loc_str, response):
# Inventory template for writing stationXML file
    inv = Inventory(
        networks=[],
        source=os.environ["UI_USER"]
    )

    

    cha = Channel(
        code=chan,
        location_code=loc_code,
        # Note that these coordinates can differ from the station coordinates.
        latitude=lat,
        longitude=lon,
        elevation=elev,
        depth=0.0,
        #azimuth=0.0,
        #dip=-90.0,
        #sample_rate=200
    )

    # Now tie it all together.
    cha.response = response
    sta.channels.append(cha)
    net.stations.append(sta)
    inv.networks.append(net)
    return inv


# Write to a StationXML file. Also force a validation against
# the StationXML schema to ensure it produces a valid StationXML file.
def create_xml():
    inv = create_inv(net, stat, lat, lon, elev, site, chan, loc_str, response)
    fname = f'{net}.{stat}.xml'
    inv.write(f'/data/inventory/ {fname}', format="stationxml", validate=True)
    return

# todo: warn override if file exists (or same net code, stat exists)
st.button("Create station XML", on_click=create_xml, type="secondary")