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
st.title('Add stations')

# Instrument and responses online catalog
# todoldeprecated: need to use v2 offline copy instead...
# todo: verify sensor and datalogger keys "depth"
nrl = NRL()

st.markdown("## Station parameters")

# todo: add validation for all inputs, min num of chars, type of chars, etc
cols1 = st.columns(7)

net = cols1[0].text_input("Network code", value="", max_chars=2, type="default", help=None, placeholder="??")
stat = cols1[1].text_input("Station code", value="", max_chars=5, type="default", help=None, placeholder="????")
lat = cols1[2].number_input("Station latitude (decimal degree)", value=44.3387, min_value=-90.0, max_value=90.0, format="%.4f") 
lon = cols1[3].number_input("Station longitude (decimal degree)", value=1.2097, min_value=-180.0, max_value=180.0, format="%.4f") 
elev = cols1[4].number_input("Ground surface elevation (m)", value=0, min_value=-414, max_value=8848, format="%d")
site = cols1[5].text_input("Station site name", value="", max_chars=64, type="default", help=None) 
net, stat, lat, lon, elev, site
#start
#end

chan = st.text_input("Channel code", value="", max_chars=3, type="default", help=None)
#cols1 = st.columns(7)
loc = st.number_input("Location code", value="min", min_value=0, max_value=99, step=None, format="%02d", help=None, placeholder="00") 
loc_str = f'{loc:02d}'
chan, loc_str
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
        source="$UI_USER"
    )

    net = Network(
        code=net,
        stations=[],
        #description="A test stations.",
        # Start-and end dates are optional.
        #start_date=obspy.UTCDateTime(2016, 1, 2)
    )

    sta = Station(
        code=sta,
        latitude=lat,
        longitude=lon,
        elevation=elev,
        #creation_date=obspy.UTCDateTime(2016, 1, 2),
        site=Site(name=site)
    )

    cha = Channel(
        code=chan,
        location_code=loc_str,
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
    inv.write("station.xml", format="stationxml", validate=True)
    return

st.button("Create XML", on_click=create_xml, type="secondary")