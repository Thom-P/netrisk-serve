"""Data and metadata fetching module for the local Seiscomp (FDSNWS) server.

Fetch stations, channels, traces, and data availability from
the local Seiscomp (FDSNWS) server through HTTP requests (Docker network).
"""

import requests
import io
import datetime

from obspy.core import UTCDateTime
from obspy.clients.fdsn.header import FDSNNoDataException
import streamlit as st
import pandas as pd

BASE_URL = 'http://seiscomp:8080/fdsnws'


# @st.cache_data  # use obspy client instead?
def fetch_stations():
    """Fetch all stations from the Seiscomp FDSNWS server."""
    suffix = '/fdsnws/station/1/query?network=*&format=text&level=station'
    try:
        data = requests.get(BASE_URL + suffix)
    except requests.exceptions.RequestException as e:
        st.error(f"Request error: {e}", icon="🚨")
        st.stop()
    if data.status_code != 200:
        st.warning(data.reason, icon="⚠️")
        return None
    text = data.content.decode('utf-8')
    return text


# @st.cache_data
def fetch_channels(net, sta):
    """Fetch all channels for a given station."""
    suffix = f'/station/1/query?' \
             f'network={net}' \
             f'&station={sta}' \
             f'&format=text' \
             f'&level=channel'
    try:
        data = requests.get(BASE_URL + suffix)
    except requests.exceptions.RequestException as e:
        st.error(f"Request error: {e}", icon="🚨")
        st.stop()
    if data.status_code != 200:
        st.warning(data.reason, icon="⚠️")
        return None
    text = data.content.decode('utf-8')
    return text


# @st.cache_data
def fetch_availability(net, sta):
    """Fetch data availability for a given station."""
    suffix = f'/availability/1/query?' \
             f'&network={net}' \
             f'&station={sta}' \
             f'&merge=overlap,samplerate,quality'
    try:
        data = requests.get(BASE_URL + suffix)
    except requests.exceptions.RequestException as e:
        st.error(f"Request error: {e}", icon="🚨")
        st.stop()
    if data.status_code != 200:
        st.write(data.reason)
        return None
    text = data.content.decode('utf-8')
    return text


def fetch_latest_data_times():
    """Fetch the most recent data timestamps for each station.

    Return a dataframe containing a color-coded status depending
    on the time elapsed since the most recent data timestamp:
    - Green light if < 1 hour
    - Yellow light if < 1 day
    - Red light if > 1 day 
    """
    suffix = '/availability/1/extent?' \
          'network=*&station=*&merge=samplerate,quality'
    try:
        data = requests.get(BASE_URL + suffix)
    except requests.exceptions.RequestException as e:
        st.error(f"Request error: {e}", icon="🚨")
        st.stop()
    if data.status_code != 200:
        st.write(data.reason)
        return None
    text = data.content.decode('utf-8')
    if text is None:
        st.info("Data availability not available", icon="ℹ️")
        return None
    df_latest = pd.read_csv(io.StringIO(text[1:]), sep=r"\s+",
                            dtype=str, usecols=['N', 'S', 'Latest'],
                            parse_dates=['Latest'])
    # need to simplify todo
    df_latest['Latest'] = pd.to_datetime(df_latest['Latest'], format='mixed',
                                         utc=True)
    # Only the most recent data (disregard loc and chans)
    df_latest = df_latest.sort_values('Latest').drop_duplicates(['N', 'S'],
                                                                keep='last')
    time_now = datetime.datetime.now(datetime.timezone.utc)
    # color code based on time of last data received:
    # green: < 1 hour, yellow: < 1 day, red: > 1 day
    df_latest['Status'] = df_latest['Latest'].apply(
        lambda x: '🟢' if (time_now - x).total_seconds() < 3600 else
                  '🟡' if (time_now - x).days < 1 else '🔴'
        )
    # df_latest.rename(columns={"N": "Network", "S": "Station",
    # "Latest": "Last data received"}, inplace=True)
    # remove Latest column (not used anymore)
    df_latest.drop(columns=['Latest'], inplace=True)
    df_latest.rename(columns={"N": "Network", "S": "Station"}, inplace=True)
    return df_latest


# @st.cache_data(show_spinner=False)
def fetch_traces(client, net, sta, loc, chans, start_date, end_date):
    """Fetch traces for a given station, location, channels, and time frame."""
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
    except requests.exceptions.RequestException as e:
        st.error(f"Request error: {e}", icon="🚨")
        st.stop()
    return waveform_stream
