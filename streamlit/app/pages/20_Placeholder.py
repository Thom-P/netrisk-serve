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
nrl = NRL()

st.write("New station")

# todo: add validation for all inputs, min num of chars, type of chars, etc
net = st.text_input("Network code", value="", max_chars=2, type="default", help=None, placeholder="??")
stat = st.text_input("Station code", value="", max_chars=5, type="default", help=None, placeholder="????")
loc = st.text_input("Location code", value="00", max_chars=2, type="default", help=None, placeholder="00") 

manufacturer = st.selectbox("Select sensor manufacturer", nrl.sensors.keys(), index=None, placeholder="Choose an option")
sensor_choice = [] if manufacturer is None else nrl.sensors[manufacturer].keys()
sensor = st.selectbox("Select sensor", sensor_choice, index=None, placeholder="Choose an option", disabled=manufacturer is None)
model = None
if sensor is not None and isinstance(nrl.sensors[manufacturer][sensor], dict):
    #model_choice = [] if sensor is None else nrl.sensors[manufacturer][sensor].keys()
    model_choice = nrl.sensors[manufacturer][sensor].keys()
    model = st.selectbox("Select model", model_choice, index=None, placeholder="Choose an option")
model

with st.form("new_station_form"):
    checkbox_val = st.checkbox("Form checkbox")

    # Every form must have a submit button.
    submitted = st.form_submit_button("Submit")
    if submitted:
        st.write("net", net, "checkbox", checkbox_val)

st.write("Outside the form")