import string

import streamlit as st
from obspy.core.inventory import Inventory, Network, Station, Channel, Site

from utils.FDSN_codes import band_codes, source_codes, subsource_codes, valid_chars


def get_station_parameters():
    code_help_str = "1 - 8 uppercase alphanumeric or dash characters"
    coord_help_str = "in decimal degrees - WGS84"

    net_url = 'http://docs.fdsn.org/projects/source-identifiers/en/v1.0/network-codes.html#'
    st.page_link(net_url, label=':blue[More info on naming conventions ↗]')

    cols1 = st.columns(6)
    net_code = cols1[0].text_input("__Network code__", value=None, max_chars=8, type="default", help=code_help_str, placeholder="Required")
    sta_code = cols1[1].text_input("__Station code__", value=None, max_chars=8, type="default", help=code_help_str, placeholder="Required")
    
    lat = cols1[2].number_input("__Station latitude__", value=None, min_value=-90.0, max_value=90.0, format="%.4f", help=coord_help_str, placeholder="Required") 
    lon = cols1[3].number_input("__Station longitude__", value=None, min_value=-180.0, max_value=180.0, format="%.4f", help=coord_help_str, placeholder="Required") 
    elev = cols1[4].number_input("__Ground surface elevation__ (m)", value=None, min_value=-414, max_value=8848, format="%d", placeholder="Required")
    
    site = cols1[5].text_input("__Station site name__", value=None, max_chars=64, type="default", help=None, placeholder="Required") 
    
    if net_code is None or is_valid_code(net_code, valid_chars) is False:
        st.warning('Invalid or empty network code', icon="⚠️")
        st.stop()
    if sta_code is None or is_valid_code(sta_code, valid_chars) is False:
        st.warning('Invalid or empty station code', icon="⚠️")
        st.stop()
    if lat is None or lon is None or elev is None:
        st.warning('Empty coordinate(s)', icon="⚠️")
        st.stop()
    if site is None or len(site) == 0: 
        st.warning('Empty site name', icon="⚠️")
        st.stop()
    return net_code, sta_code, lat, lon, elev, site

def is_valid_code(code, valid_chars):
    # Following norm: http://docs.fdsn.org/projects/source-identifiers/en/v1.0/definition.html
    if len(code) < 1 or len(code) > 8:
        return False
    if any(c not in valid_chars for c in code):
        return False
    return True

def build_station_and_network_objects(net_code, sta_code, lat, lon, elev, site):
    sta = Station(
            code=sta_code,
            latitude=lat,
            longitude=lon,
            elevation=elev,
            site=Site(name=site)
    )
    net = Network(code=net_code, stations=[sta])
    return net, sta

def get_channel_codes():
    cols2 = st.columns(3)
    code_dicts = (band_codes, source_codes, subsource_codes)
    labels = (
        "__Band code__ - fs: sample rate (Hz); Tc: lower period bound of instrument response (s)",
        "__Source code (instrument type)__",
        "__Subsource code(s) (components)__"
    )
    code_choices = []
    for i, code_dict in enumerate(code_dicts):
        code = cols2[i].selectbox(
            labels[i],
            code_dict,
            index=None, 
            format_func=lambda code: f'{code} - {code_dict[code]}'
        )
        if code is None:
            st.stop()
        code_choices.append(code)
    band_code, source_code, subsource_code = code_choices
    return band_code, source_code, subsource_code 

def choose_device(device_dict, device_type: str):
    ## Device choice (sensor or datalogger)
    # todo make sure max depth is not greater than 6
    st.markdown(f"### {device_type}")
    cols = st.columns(6, vertical_alignment="bottom")
    i_col = 0
    device_keys=[]
    curr_choices = device_dict
    while isinstance(curr_choices, dict):
        col = cols[i_col]
        choice = create_selectbox(curr_choices, col)
        i_col += 1
        if choice is None:
            st.stop()
        else:
            device_keys.append(choice)
            curr_choices = curr_choices[choice]
    return device_keys

def create_selectbox(choices: dict, col):
    label = choices.__str__().partition('(')[0]
    choice = col.selectbox(label, choices.keys(), index=None, placeholder="Choose an option")
    return choice

def build_channel_objects(band_code, source_code, subsource_code, response, sta, ph):
    channel_objs = []
    code_help_str = "1 - 8 uppercase alphanumeric or dash characters"
    coord_help_str = "in decimal degrees - WGS84"
    subsource_code_list = subsource_code.split(', ')
    cols = ph.columns(len(subsource_code_list))
    for i, sub_code in enumerate(subsource_code_list):
        cont = cols[i].container(border=True)
        chan_code = '_'.join((band_code, source_code, sub_code))
        with cont:
            st.write(f"__Channel {chan_code}__")
            value = st.session_state[f"loc_chan_{i}"] if f"loc_chan_{i}" in st.session_state else "00"
            loc_code = st.text_input("Location code", value=value, max_chars=8, type="default", help=code_help_str, key=f"loc_chan_{i}")
            
            chan_lat = st.number_input("__Channel latitude__", value=sta.latitude, min_value=-90.0, max_value=90.0, format="%.4f", help=coord_help_str, key=f"lat_chan_{i}") 
            
            chan_lon = st.number_input("__Channel longitude__", value=sta.longitude, min_value=-180.0, max_value=180.0, format="%.4f", help=coord_help_str, key=f"lon_chan_{i}") 
            
            chan_depth = st.number_input("__Sensor depth__ (m)", value=0, min_value=-1000, max_value=10000, format="%d", help="Positive value for buried sensors", key=f"depth_chan_{i}")
            
            chan_elev = sta.elevation - chan_depth
            #st.write(f"__Sensor elevation__ = {chan_elev} m") # warning: confusing, value not updated until add chan, do not display or investigate 
            #st.number_input("__Sensor elevation__ (m)", value=elev, min_value=-10000, max_value=10000, format="%d", help="Should correspond to ground elevation minus depth", key=f'elev{band_code}{source_code}{sub_code}')
        cha = Channel(
            code=chan_code,
            location_code=loc_code,
            # Note that these coordinates can differ from the station coordinates.
            latitude=chan_lat,
            longitude=chan_lon,
            elevation=chan_elev,
            depth=chan_depth,
            response=response,
            #azimuth=0.0,
            #dip=-90.0,
            #sample_rate=200
        )
        channel_objs.append(cha)
    return channel_objs


##################################################
#class Instrument:
#    def __init__(self):
#        self.sensor_keys = None
#        self.datalogger_keys = None
#        self.response = None
#        self.channels = []

#class StationXML:
#    def __init__(self):
#        self.params