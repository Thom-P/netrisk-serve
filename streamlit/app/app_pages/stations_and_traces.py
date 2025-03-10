"""Application main page, for stations inventory and traces visualization.

Divide screen into two columns, provide three tabs on left column:
- Stations: display a table of stations info and status. Upon station
selection, show detailed information about channels and data availability.
- Trace: get user input for location, channel(s), and time window.
Allow optional filtering and response removal. Display traces in interactive
plot. Allow trace download in various formats.
- Day plot: get user input for location, single channel, and day. Show
corresponding a day plot (24h of data in one figure).
Display a map of all stations on the right column.
"""
import io

import pandas as pd
import streamlit as st
from streamlit import session_state as sstate
from streamlit_folium import st_folium
from obspy.clients.fdsn import Client

from utils.data_fetch import (
    fetch_stations,
    fetch_traces,
    fetch_latest_data_times
)
from utils.station_map import create_map, get_map_column_width
from utils.station_infos import display_channels, display_availability
from utils.trace_view import (
    select_channels_and_dates,
    select_day_plot_params,
    select_filter_params,
    preprocess_traces,
    plot_traces,
    download_trace,
)


st.header('Stations and traces')  # st.title too big
try:
    client = Client("http://seiscomp:8080")
except Exception as e:
    st.error(f"Connection error to FDSN server: {e}", icon="🚨")
    st.stop()

# Fetch stations info and populate dataframe if not already done
if "df_stations" not in sstate:
    stations_txt = fetch_stations()
    if stations_txt is None:
        st.info(
            "You first need to create a station XML file and an FTP account "
            "for each of your stations.",
            icon="ℹ️"
        )
        st.stop()
    # Prevent auto conversion to int when names are only numbers
    resp_types = {
        'Network': str,
        'Station': str,
        'SiteName': str
    }
    # Remove first char '#' (header line included as comment)
    sstate.df_stations = pd.read_csv(
        io.StringIO(stations_txt[1:]), sep='|', dtype=resp_types
    )
    sstate.df_stations["EndTime"].fillna("Active", inplace=True)
    # Fetch status (latest time data was received for each station)
    df_latest = fetch_latest_data_times()
    # Insert status in df_stations
    if df_latest is not None:
        sstate.df_stations = sstate.df_stations.merge(
            df_latest, how='left', on=['Network', 'Station']
        )
        sstate.df_stations['Status'].fillna('⚫', inplace=True)
    else:
        sstate.df_stations['Status'] = '❓'
    # Set Status as first column
    cols = sstate.df_stations.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    sstate.df_stations = sstate.df_stations[cols]

# use client instead?
# inv = client.get_stations(level="station")  # combine with previous fetch ?
# net_codes = {net.code: ind for ind, net in enumerate(inv.networks)}
# # need to test if empty


# Station map
map = create_map()

data_column, map_column = st.columns([0.6, 0.4])
with map_column:
    st.text("")  # Hack for pseudo alignment of map
    map_data = st_folium(map, width=get_map_column_width(),
                         returned_objects=[])
    # call to render Folium map in Streamlit, but don't get any data back
    # from the map (so that it won't rerun the app when the user interacts)
    # disabled interactivity because absence of on_click callable makes synchro
    # with df very convoluted (could try with updating keys to refresh map
    # select and df select)

station_tab, trace_tab, day_plot_tab = data_column.tabs(
    ["Stations", "Trace", "Day plot"]
)

net, sta = None, None


# ****** Station information tab
with station_tab:
    status_help = (
        "Last data received: 🟢 - under an hour ago; 🟡 - under a day ago; "
        "🔴 - over a day ago; ⚫ - no data"
    )
    # Display stations as dataframe and get selection events
    event = st.dataframe(
        sstate.df_stations,
        hide_index=True,
        key=None,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Status": st.column_config.TextColumn(
                "Status ⓘ",
                help=status_help,
            )
        }
    )

    # Station selection in dataframe
    row_index = None
    if 'selection' in event and 'rows' in event['selection'] and \
            (row_index := event['selection']['rows']):
        net, sta = sstate.df_stations.iloc[row_index[0]][[
            'Network', 'Station'
        ]]
        with st.expander('Channels'):
            display_channels(net, sta)
        with st.expander('Data availability'):
            display_availability(net, sta)
    else:
        st.info(
            "Select station by ticking box in the leftmost column.",
            icon="ℹ️"
        )


# ****** Trace viewer
with trace_tab:
    if sta is None:
        st.write('Select a station in the previous tab.')
    else:
        st.markdown(f'## {net}.{sta}')
        loc, chans, start_date, end_date = select_channels_and_dates()

        # Optional filter
        fmin, fmax = None, None
        filt_msg = "Applies linear detrend, taper, and a 4th order " \
            "Butterworth bandpass filter."
        if st.checkbox('Apply filter', help=filt_msg, key='trace_filter_box'):
            fmin, fmax = select_filter_params(loc, chans, key="trace_filter")

        # Optional response removal
        resp_msg = (
            "The deconvolution involves mean removal, cosine tapering in time"
            " domain (5%), and the use of a water level (60 dB) to clip the "
            "inverse spectrum and prevent noise overamplification (see obspy)."
        )
        resp_remove = st.checkbox('Remove instrument response', help=resp_msg)

        if st.button('View Trace', disabled=False if chans else True):
            with st.spinner('Fetching traces...'):
                traces = fetch_traces(
                    client, net, sta, loc, ','.join(chans),
                    start_date, end_date
                )
                if traces is None:
                    sstate.traces = None
                    st.stop()
            sstate.traces = preprocess_traces(traces, fmin, fmax, resp_remove)

            if sstate.traces is not None:
                with st.spinner('Loading plot...'):
                    # Width will be auto adjusted to fit column container
                    height = 200 + 300 * len(chans)
                    plot_traces(sstate.traces, resp_remove, height)

                download_trace(
                    net, sta, loc, chans, start_date, end_date, fmin, fmax
                )

# ****** Day plot
with day_plot_tab:
    if sta is None:
        st.write('Select a station in the previous tab.')
    else:
        st.markdown(f'## {net}.{sta}')
        loc, chan, start_date, end_date = select_day_plot_params()
        st.info("A linear detrend is applied to all traces for better \
                visualization.", icon="ℹ️")
        fmin, fmax = None, None
        filt_msg = "Applies linear detrend, taper, and a 4th order " \
            "Butterworth bandpass filter."
        if st.checkbox('Apply filter', help=filt_msg, key="day_filter_box"):
            fmin, fmax = select_filter_params(loc, [chan], key="day_filter")
        # TODO: add validity check vs fs

        if "day_traces" not in sstate:
            sstate.day_traces = None
        disable_day_plot = True if chan is None else False
        if st.button('View day plot', disabled=disable_day_plot):
            with st.spinner('Fetching traces...'):
                traces = fetch_traces(
                    client, net, sta, loc, chan, start_date, end_date
                )
                if traces is None:
                    sstate.day_traces = None
                    st.stop()

            if fmin is not None and fmax is not None:
                sstate.day_traces = preprocess_traces(traces, fmin, fmax,
                                                      resp_remove=False)
            else:
                traces.detrend("linear")  # Necessary for decent visualization
                sstate.day_traces = traces
            if sstate.day_traces is not None:
                with st.spinner('Loading plot...'):
                    date_str = start_date.strftime("%A %d %B %Y")
                    # prev_col, date_col, next_col = st.columns(3)  #TODO?
                    # if prev_col.button('◀️'):
                    st.markdown(
                        f'<div style="text-align: center;">{date_str}</div>',
                        unsafe_allow_html=True
                    )
                    # if next_col.button('▶️')
                    fig = sstate.day_traces.plot(handle=True, type='dayplot')
                    st.pyplot(fig)
