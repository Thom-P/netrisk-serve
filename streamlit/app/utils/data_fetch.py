import requests
from obspy.core import UTCDateTime
from obspy.clients.fdsn.header import FDSNNoDataException
import streamlit as st
import folium

#@st.cache_data  # use obspy client instead?
def fetch_stations():
    url = 'http://seiscomp:8080/fdsnws/station/1/query?' \
        'network=*&format=text&level=station'
    try:
        data = requests.get(url)
    except FDSNNoDataException:
        st.warning('No station found.', icon="⚠️")
        return None
    if data.status_code != 200:
        st.warning(data.reason, icon="⚠️")
        return None
    text = data.content.decode('utf-8')
    return text


#@st.cache_data
def fetch_channels(net, sta):
    url = f'http://seiscomp:8080/fdsnws/station/1/query?' \
        f'network={net}' \
        f'&station={sta}' \
        f'&format=text' \
        f'&level=channel'
    data = requests.get(url)
    if data.status_code != 200:
        st.write(data.reason)
        return None
    text = data.content.decode('utf-8')
    return text

#@st.cache_data
def fetch_availability(net, sta):
    #f'starttime=2024-09-01T00%3A00%3A00' \
    #f'&endtime=2024-09-27T00%3A00%3A00' \
    url = f'http://seiscomp:8080/fdsnws/availability/1/query?' \
          f'&network={net}' \
          f'&station={sta}' \
          f'&merge=overlap,samplerate,quality'
    data = requests.get(url)
    if data.status_code != 200:
        st.write(data.reason)
        return None
    text = data.content.decode('utf-8')
    return text

#@st.cache_data(show_spinner=False)
def get_trace(client, net, sta, loc, chans, start_date, end_date):
    try:
        waveform_stream = client.get_waveforms(
            net,
            sta,
            loc,
            chans,
            UTCDateTime(start_date),
            UTCDateTime(end_date),
            attach_response=True
            )
    except FDSNNoDataException:
        st.warning('No data found for the requested period.', icon="⚠️")
        return None
    except Exception as e:
        st.exception(e)
        # print(f"Unexpected {err=}, {type(err)=}")
        return None
    return waveform_stream

