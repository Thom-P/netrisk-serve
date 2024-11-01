import io
import datetime

import streamlit as st
import pandas as pd
from streamlit import session_state as sstate
from streamlit_folium import st_folium
from obspy.clients.fdsn import Client

from utils.obspy_plot_mod import ModifiedWaveformPlotting
from utils.data_fetch import fetch_stations, get_trace, fetch_latest_data_times
from utils.station_map import create_map, get_map_col_width
from utils.station_infos import display_channels, display_availabilty
from utils.trace_view import (
    select_channels_and_dates,
    select_filter_params,
    fetch_trace_units,
    download_trace,
    preprocess_traces,
)


st.header('Stations and traces')  # st.title too big

client = Client("http://seiscomp:8080")  # todo connection test here


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


# Map
m = create_map()

col1, col2 = st.columns([0.6, 0.4])
with col2:
    st.text("")  # Hack for pseudo alignment of map
    map_data = st_folium(m, width=get_map_col_width(), returned_objects=[])
    # call to render Folium map in Streamlit, but don't get any data back
    # from the map (so that it won't rerun the app when the user interacts)
    # disabled interactivity because absence of on_click callable makes synchro
    # with df very convoluted (could try with updating keys to refresh map
    # select and df select)

tab1, tab2, tab3 = col1.tabs(["Station info", "Trace", "Day plot"])

net, sta = None, None

# ****** Station info
with tab1:
    status_help = (
        "Last data received: 🟢 - under an hour ago; 🟡 - under a day ago; "
        "🔴 - over a day ago; ⚫ - no data"
    )
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
    if 'selection' in event and 'rows' in event['selection']:
        row_index = event['selection']['rows']
    # row_index = event.selection['rows']
    if not row_index:
        st.info(
            "Select station by ticking box in the leftmost column.",
            icon="ℹ️"
        )
    else:
        net, sta = sstate.df_stations.iloc[row_index[0]][[
            'Network', 'Station'
        ]]
        with st.expander('Channels'):
            display_channels(net, sta)
        with st.expander('Data availability'):
            display_availabilty(net, sta)


# ****** Trace viewer
with tab2:
    if sta is None:
        st.write('Select a station in the previous tab.')
    else:
        st.markdown(f'## {net}.{sta}')
        loc, chans, start_date, end_date = select_channels_and_dates()

        fmin, fmax = None, None
        filt_msg = "Applies linear detrend, taper, and a 4th order " \
            "Butterworth bandpass filter."
        if st.checkbox('Apply filter', help=filt_msg):
            fmin, fmax = select_filter_params(loc, chans, key="trace_filter")
        resp_msg = (
            "The deconvolution involves mean removal, cosine tapering in time"
            " domain (5%), and the use of a water level (60 dB) to clip the "
            "inverse spectrum and prevent noise overamplification (see obspy)."
        )
        resp_remove = st.checkbox('Remove instrument response', help=resp_msg)

        if st.button('View Trace', disabled=False if chans else True):
            with st.spinner('Fetching traces...'):
                traces = get_trace(
                    client, net, sta, loc, ','.join(chans),
                    start_date, end_date
                )
                if traces is None:
                    sstate.traces = None
                    st.stop()
            sstate.traces = preprocess_traces(traces, fmin, fmax, resp_remove)

            if sstate.traces is not None:
                with st.spinner('Loading plot...'):
                    # nb: width will be adjusted to fit column container
                    height = 200 + 300 * len(chans)
                    width = height
                    waveform = ModifiedWaveformPlotting(
                        stream=sstate.traces, handle=True, size=(width, height)
                    )
                    fig = waveform.plot_waveform(handle=True)
                    units = fetch_trace_units(sstate.traces[0], resp_remove)
                    fig.add_annotation(
                        text=f"Amplitude ({units})", textangle=-90,
                        xref='paper', xanchor='right', xshift=-90,
                        x=0, yref='paper', y=0.5, showarrow=False
                    )
                    st.plotly_chart(fig, use_container_width=True, theme=None)
                    st.info(
                        f"Traces including more than {waveform.max_npts} samples "
                        f"({int(waveform.max_npts / 100 / 60)} mins at 100Hz) are plotted "
                        "using the low resolution min/max method (add ref). To interact "
                        "with the fully resolved data, reduce the time window.",
                        icon="ℹ️"
                    )

                download_trace(
                    net, sta, loc, chans, start_date, end_date, fmin, fmax
                )



    # Easier to keep traces separated and download separately?,
    # could also use a zip archive
    # for trace in traces:
    #    id = trace.get_id()
    #    id
    #    if fmin is not None and fmax is not None:
    #        fname = f'{id}_{start_date.isoformat()}_{end_date.isoformat()}_bandpassed_{fmin}Hz_{fmax}Hz.mseed' # replace with actual dates
    #    else:
    #        fname = f'{id}_{start_date.isoformat()}_{end_date.isoformat()}.mseed' # replace with actual dates
    #    file_buff = io.BytesIO()
    #    trace.write(file_buff, format="MSEED") # select appropriate encoding? nb: filehandle instead of filename also works!
    #    # need a unique key otherwise error
    #    st.download_button(label=f'Download {trace.meta.channel} trace', data=file_buff, file_name=fname, type="secondary", help='Note that filtered traces are much larger than their unfiltered counterparts (compressed digital counts).')





# ########### Day plot
with tab3:  # need indep vars?
    if sta is None: 
        st.write('Select a station in the previous tab.')
    else: 
        st.markdown(f'## {net}.{sta}')
        
        col31, col32 = st.columns(2)
        loc_codes = sorted(sstate.channel_df['Location'].unique().tolist())
        loc = col31.selectbox("Select location", loc_codes, key="loc_day_plot")
        chan_codes = sstate.channel_df.query('Location == @loc')['Channel'].unique(
        ).tolist()
        chan = col32.selectbox("Select channel", chan_codes)
        # sstate['chans'] = st.multiselect("Select channel(s)", chan_codes)
        # chans = sstate['chans']

        day = st.date_input('Day', value="default_value_today")
        start_date = datetime.datetime(day.year, day.month, day.day)
        end_date = start_date + datetime.timedelta(hours=24)
        
        fmin, fmax = None, None
        filt_msg = "Applies linear detrend, taper, and a 4th order " \
            "Butterworth bandpass filter."
        if st.checkbox('Apply day filter', help=filt_msg):
            fmin, fmax = select_filter_params(loc, [chan], key="day_filter")
        #   # add validity check vs fs


        if "day_traces" not in sstate:
            sstate.day_traces = None
        if st.button('View day plot', disabled=True if chan is None else False):
            with st.spinner('Fetching traces...'):
                traces = get_trace(client, net, sta, loc, chan, start_date, end_date)
                if traces is None:
                    sstate.day_traces = None
                    st.stop()
            
            traces.detrend("linear") # otherwise cannot see anything
            
            if fmin is not None and fmax is not None:
                with st.spinner('Filtering...'):
                    traces.taper(max_percentage=0.05)
                    traces.filter("bandpass", freqmin=fmin, freqmax=fmax)
            
            #traces.merge(method=1)

            sstate.day_traces = traces
            # add info about these preprocesses 
            if sstate.day_traces is not None:
                with st.spinner('Loading plot...'): 
                    fig = sstate.day_traces.plot(handle=True, type='dayplot')
                    # fig.axes[-1].set_xlabel('Time')
                    # fig.axes[-1].set_ylabel('Counts')

                    st.pyplot(fig)



## Side bar selections
#sstate['net'] = None
#sstate['sta'] = None
#sstate['chans'] = set()

#with st.sidebar:
#    #index_preselect = net_codes[sstate['net']] if sstate['net'] is not None else None
#    # widget should handle session state
#    sstate['net'] = st.selectbox('Network', net_codes.keys(), placeholder="Choose a Network")
#    net = sstate['net']
#    inv_stations = []
#    if net is not None:
#        inv_stations = inv.networks[net_codes[net]].stations
#    sta_codes = (sta.code for sta in inv_stations)
#    sstate['sta'] = st.selectbox('Station', sta_codes, placeholder="Choose a Station")
#    sta = sstate['sta']
#    inv_detailed = None
#    if sta is not None:
#        inv_detailed = client.get_stations(network=net, station=sta, level="channel")
#    chan_codes = set(chan.code for chan in inv_detailed.networks[0].stations[0]) if inv_detailed is not None else set()
#    sstate['chans'] = st.multiselect("Select channel(s)", chan_codes)
#    chans = sstate['chans']

## Matplot lib plots
# fig = plt.figure()
# plt.plot([1, 2, 3], [4, 5, 6])
# st.pyplot(fig)
# #traces.plot(fig=fig)

#fig = sstate.traces.plot(handle=True)
#fig.axes[-1].set_xlabel('Time')
#fig.axes[-1].set_ylabel('Counts')
#st.pyplot(fig)

# This below causes logic issue (radio button not showing in fragment, why?)
#fig_html = mpld3.fig_to_html(fig)
#components.html(fig_html, height=600)
 