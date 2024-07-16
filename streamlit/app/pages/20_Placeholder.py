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

st.markdown("## Station parameters")

# todo: add validation for all inputs, min num of chars, type of chars, etc
cols1 = st.columns(3)

net = cols1[0].text_input("Network code", value="", max_chars=2, type="default", help=None, placeholder="??")
stat = cols1[1].text_input("Station code", value="", max_chars=5, type="default", help=None, placeholder="????")
loc = cols1[2].text_input("Location code", value="00", max_chars=2, type="default", help=None, placeholder="00") 
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

with st.form("new_station_form"):
    checkbox_val = st.checkbox("Form checkbox")

    # Every form must have a submit button.
    submitted = st.form_submit_button("Submit")
    if submitted:
        st.write("net", net, "checkbox", checkbox_val)

st.write("Outside the form")