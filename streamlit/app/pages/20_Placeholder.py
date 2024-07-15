import streamlit as st
from obspy.clients.nrl import NRL

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

st.write("New station")

# todo: add validation for all inputs, min num of chars, type of chars, etc
net = st.text_input("Network code", value="", max_chars=2, type="default", help=None, placeholder="??")
stat = st.text_input("Station code", value="", max_chars=5, type="default", help=None, placeholder="????")
loc = st.text_input("Location code", value="00", max_chars=2, type="default", help=None, placeholder="00") 

sensor_manufacturer = st.selectbox("Select sensor manufacturer", nrl.sensors.keys(), index=None, placeholder="Choose an option")
sensors = [] if sensor_manufacturer is None else nrl.sensors[sensor_manufacturer].keys()
sensor = st.selectbox("Select sensor", sensors, index=None, placeholder="Choose an option", disabled=sensor_manufacturer is None)
sensor_param = None
if sensor is not None and isinstance(nrl.sensors[sensor_manufacturer][sensor], dict):
    sensor_params = nrl.sensors[sensor_manufacturer][sensor].keys()
    sensor_param = st.selectbox(nrl.sensors[sensor_manufacturer][sensor].__str__(), sensor_params, index=None, placeholder="Choose an option")
sensor_param
ADC_manufacturer = st.selectbox("Select digitizer manufacturer", nrl.dataloggers.keys(), index=None, placeholder="Choose an option")
ADCs = [] if ADC_manufacturer is None else nrl.dataloggers[ADC_manufacturer].keys()
ADC = st.selectbox("Select digitizer", ADCs, index=None, placeholder="Choose an option", disabled=ADC_manufacturer is None)
ADC_gain = None
if ADC is not None and isinstance(nrl.dataloggers[ADC_manufacturer][ADC], dict):
    ADC_gains = nrl.dataloggers[ADC_manufacturer][ADC].keys()
    ADC_gain = st.selectbox(nrl.dataloggers[ADC_manufacturer][ADC].__str__(), ADC_gains, index=None, placeholder="Choose an option")
ADC_sample_rate = None
if ADC_gain is not None and isinstance(nrl.dataloggers[ADC_manufacturer][ADC][ADC_gain], dict):
    ADC_sample_rates = nrl.dataloggers[ADC_manufacturer][ADC][ADC_gain].keys()
    ADC_sample_rate = st.selectbox(nrl.dataloggers[ADC_manufacturer][ADC][ADC_gain].__str__(), ADC_sample_rates, index=None, placeholder="Choose an option")

response = nrl.get_response(
    sensor_keys=[sensor_manufacturer, sensor, sensor_param],
    datalogger_keys=[ADC_manufacturer, ADC, ADC_gain, ADC_sample_rate]
)
response

with st.form("new_station_form"):
    checkbox_val = st.checkbox("Form checkbox")

    # Every form must have a submit button.
    submitted = st.form_submit_button("Submit")
    if submitted:
        st.write("net", net, "checkbox", checkbox_val)

st.write("Outside the form")