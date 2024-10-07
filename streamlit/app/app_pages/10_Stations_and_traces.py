import io
import datetime
#import math
import copy

import streamlit as st
import streamlit.components.v1 as components
import folium
import pandas as pd
#import mpld3
from streamlit_folium import st_folium
from streamlit_dimensions import st_dimensions
# from obspy import read
from obspy.clients.fdsn import Client
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go

from utils.obspy_plot_mod import ModifiedWaveformPlotting
#from utils.trace_plot import plot_traces
from utils.data_fetch import fetch_stations, get_trace
from utils.station_map import create_map
from utils.station_infos import display_channels, display_availabilty

#st.title('Stations and traces')
st.header('Stations and traces')

client = Client("http://seiscomp:8080")  # todo connection test here


if "df_stations" not in st.session_state:
    stations_txt = fetch_stations()
    if stations_txt is None:
        st.info("You first need to create a station XML file and an FTP account for each of your stations.", icon="ℹ️")
        st.stop()
    resp_types = {'Network': str, 'Station': str, 'SiteName': str} # to prevent auto conversion to int when num only names
    st.session_state.df_stations = pd.read_csv(io.StringIO(stations_txt[1:]), sep='|', dtype=resp_types)
    # remove first char '#' (header line included as comment)

#inv = client.get_stations(level="station")  # can cache ? combine with previous fetch ?
#net_codes = {net.code: ind for ind, net in enumerate(inv.networks)}  # need to test if empty

#st.session_state['net'] = None
#st.session_state['sta'] = None
#st.session_state['chans'] = set()

#with st.sidebar:
#    #index_preselect = net_codes[st.session_state['net']] if st.session_state['net'] is not None else None
#    # widget should handle session state
#    st.session_state['net'] = st.selectbox('Network', net_codes.keys(), placeholder="Choose a Network")
#    net = st.session_state['net']
#    inv_stations = []
#    if net is not None:
#        inv_stations = inv.networks[net_codes[net]].stations
#    sta_codes = (sta.code for sta in inv_stations)
#    st.session_state['sta'] = st.selectbox('Station', sta_codes, placeholder="Choose a Station")
#    sta = st.session_state['sta']
#    inv_detailed = None
#    if sta is not None:
#        inv_detailed = client.get_stations(network=net, station=sta, level="channel")
#    chan_codes = set(chan.code for chan in inv_detailed.networks[0].stations[0]) if inv_detailed is not None else set()
#    st.session_state['chans'] = st.multiselect("Select channel(s)", chan_codes)
#    chans = st.session_state['chans']

# Map
m = create_map()

@st.fragment
def get_map_col_width():
    width=st_dimensions(key="map_col")
    return width

col1, col2 = st.columns([0.6, 0.4])
with col2:
    st.text("") # hack for pseudo alignment of map
    #st.write('test')
    map_data = st_folium(m, width=get_map_col_width(), returned_objects=[])
    # call to render Folium map in Streamlit, but don't get any data back
    # from the map (so that it won't rerun the app when the user interacts)
    # disabled interactivity because absence of on_click callable makes synchro
    # with df very convoluted (could try with updating keys to refresh map
    # select and df select)

tab1, tab2, tab3 = col1.tabs(["Station info", "Trace", "Day plot"])


net, sta = None, None

#### Station info
with tab1:
    event = st.dataframe(
        st.session_state.df_stations,
        hide_index=True,
        key=None,
        on_select="rerun",
        selection_mode="single-row",
    )

    # Station selection in dataframe
    row_index = event.selection['rows']
    if not row_index:
        st.info("Select station by ticking box in the leftmost column.", icon="ℹ️")
    else:
        net, sta = st.session_state.df_stations.iloc[row_index[0]][['Network', 'Station']]
        with st.expander('Channels'):
            display_channels(net, sta)
        with st.expander('Data availability'):
            display_availabilty(net, sta)
        
###

#@st.fragment # this only work if output stored in session state: need to rethink how to handle fragment logic
def select_channels_and_dates():
    col1, col2 = st.columns(2)
    loc_codes = sorted(st.session_state.channel_df['Location'].unique().tolist())
    loc = col1.selectbox("Select location", loc_codes) # add 2 digit format
    sub_df = st.session_state.channel_df.query('Location == @loc')
    chan_codes = sub_df['Channel'].unique().tolist()
    chans = col2.multiselect("Select channel(s)", chan_codes)

    col3, col4, col5, col6 = st.columns(4)
    start_day = col3.date_input('Start Date', value="default_value_today")
    start_time = col4.time_input(
        'Start Time',
        value=datetime.time(0, 0),
        step=3600
    )
    end_day = col5.date_input(
        'End Date',
        value="default_value_today",
        min_value=None,
        max_value=None,
        key=None,
        help=None,
        on_change=None,
        format="YYYY/MM/DD",
        disabled=False,
        label_visibility="visible"
    )
    end_time = col6.time_input(
        'End Time',
        value=datetime.time(0, 0),
        step=3600
    )

    start_date = datetime.datetime.combine(start_day, start_time)
    end_date = datetime.datetime.combine(end_day, end_time)
    return loc, chans, start_date, end_date 

def select_filter_params():
    # get min fs from all selected channels
    sub_df = st.session_state.channel_df.query('Location == @loc')
    min_fs = sub_df[sub_df['Channel'].isin(chans)]['SampleRate'].min() # should test
    unit = st.radio(
        "Units",
        ["Frequency", "Period"],
        label_visibility="collapsed",
        horizontal = True
    )

    col27, col28 = st.columns(2)
    if unit == "Frequency":
        fmin = col27.number_input(
                    'Lower Freq. (Hz)',
                    min_value=0.,
                    max_value=min_fs * 0.45,
                )
        fmax = col28.number_input(
                    'Higher Freq. (Hz)',
                    min_value=fmin,
                    max_value=min_fs * 0.45,
                )
    else:
        tmin = col27.number_input(
                    'Lower Period (s)',
                    min_value=1. / (0.45 * min_fs),
                    max_value=100000.,
        )

        tmax = col28.number_input(
            'Upper Period (s)',
            min_value=tmin,
            max_value=100000.,
        )
        fmax = 1./ tmin
        fmin = 1. / tmax

    # todo: add validity check vs fs
    return fmin, fmax

        

#### Trace viewer
with tab2:
    #c.markdown(f'## {net}.{sta}')
    
    if sta is None:
        st.write('Select a station in the previous tab.')
        st.stop()

   
    loc, chans, start_date, end_date = select_channels_and_dates()

    fmin, fmax = None, None
    filt_msg = "Applies a linear detrend and a 4th order " \
        "Butterworth bandpass filter."
    if st.checkbox('Apply filter', help=filt_msg):
        fmin, fmax = select_filter_params()
            
    resp_msg = "The deconvolution involves mean removal, cosine tapering in time domain (5%), " \
        "and the use of a water level (60 dB) to clip the inverse spectrum and prevent noise overamplification (see obspy)."
    resp_remove = st.checkbox('Remove instrument response', help=resp_msg)
    #fig_deconv = plt.figure()
    #resp_plot_buffer = io.BytesIO()
    
    if "traces" not in st.session_state:
        st.session_state.traces = None
    if st.button('View Trace', disabled=False if chans else True):
        with st.spinner('Fetching traces...'):
            traces = get_trace(
                client,
                net, sta, loc,
                ','.join(chans),
                start_date, end_date
                )
            if traces is None:
                st.session_state.traces = None
                st.stop()
        if fmin is not None and fmax is not None:
            with st.spinner('Filtering...'):
                traces.detrend("linear")
                traces.filter("bandpass", freqmin=fmin, freqmax=fmax)
        if resp_remove:
            with st.spinner('Removing instrument response...'):
                try:
                    traces.detrend("linear")
                    traces.remove_response(output='DEF', water_level=60, pre_filt=None, zero_mean=True, taper=True, taper_fraction=0.05, plot=False, fig=None)
                    # plot bugs
                    #traces.remove_response(output='DEF', water_level=60, pre_filt=None, zero_mean=True, taper=True, taper_fraction=0.05, plot=True, fig=fig_deconv)
                except Exception as err:
                    st.error(err, icon="🚨")
                    st.stop()
        st.session_state.traces = traces
        if st.session_state.traces is not None:

            # fig = plt.figure()
            # plt.plot([1, 2, 3], [4, 5, 6])
            # st.pyplot(fig)
            # #traces.plot(fig=fig)
            # st.write('testend')

            #fig = st.session_state.traces.plot(handle=True)
            #fig.axes[-1].set_xlabel('Time')
            #fig.axes[-1].set_ylabel('Counts')
            #st.pyplot(fig)
            
            # This below causes logic issue (radio button not showing in fragment, why?)
            #fig_html = mpld3.fig_to_html(fig)
            #components.html(fig_html, height=600)
            

            # test obspy plot lib replacement
            # nb: size (width, height), width will be adjusted to fit column container
            height = 300 * len(chans)
            width = height
            waveform = ModifiedWaveformPlotting(stream=st.session_state.traces, handle=True, size=(width, height))
            fig = waveform.plot_waveform(handle=True)
            st.plotly_chart(fig, use_container_width=True, theme=None)
            st.info(f"Traces including more than {waveform.max_npts} samples ({int(waveform.max_npts / 100 / 60)} mins at 100Hz) are plotted using the low resolution min/max method (add ref). To interact with the fully resolved data, reduce the time window.", icon="ℹ️")


            @st.fragment
            def download_trace():
                #file_format = st.radio("Select file format", ["MSEED", "SAC", "SEGY"])
                file_format = st.radio("Select file format", ["MSEED", "SAC"])
                if file_format == "SAC":
                    # should only be one trace, and with gap value filled
                    if len(chans) > 1:
                        st.info("SAC files can only contain single component data.", icon="ℹ️")
                        st.stop()
                    
                    st.info("If present, overlapping traces are merged using the lastest of the redundant values, and gaps are filled with 0.", icon="ℹ️")
                    trace_merged = copy.deepcopy(st.session_state.traces)
                    trace_merged.merge(method=1, fill_value=0) # in place op, method use most recent value when overlap, and 0 as fill value
                # Save all Traces into 1 file?
                # should get actual earliest start and latest end times
                chans_str = '_'.join(chans)
                stream_id = f'{net}.{sta}.{loc}.{chans_str}'
                if fmin is not None and fmax is not None:
                    fname = f'{stream_id}_{start_date.isoformat()}_' \
                        f'{end_date.isoformat()}_bandpassed_{fmin}Hz_' \
                        f'{fmax}Hz'  # replace with actual dates
                else:
                    fname = f'{stream_id}_{start_date.isoformat()}_' \
                        f'{end_date.isoformat()}'
                    # replace with actual dates
                file_buff = io.BytesIO()

                if file_format == "MSEED":
                    st.session_state.traces.write(file_buff, format=file_format) # select appropriate encoding? nb: filehandle instead of filename also works!
                elif file_format == "SAC":
                    trace_merged.write(file_buff, format=file_format) # select appropriate encoding? nb: filehandle instead of filename also works!
                #elif file_format == "SEGY":
                #    try:
                #        st.session_state.traces.write(file_buff, format=file_format) 
                #    except Exception as err:
                #        st.error(f"{err}", icon="🚨")
                #        st.stop()
                #    #raise

                # select appropriate encoding?
                dl_msg = 'Note that filtered traces are much larger than their ' \
                    'unfiltered counterparts (compressed digital counts).'
                st.download_button(
                    label='Download trace(s)',
                    data=file_buff,
                    file_name=".".join([fname, file_format.lower()]),
                    type="secondary",
                    help=dl_msg
                )

            download_trace()






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
    # need to cleanup widget duplications
    #c.markdown(f'## {net}.{sta}')
    
    if sta is None: 
        st.write('Select a station in the previous tab.')
        st.stop()
    
    col31, col32 = st.columns(2)
    loc_codes = sorted(st.session_state.channel_df['Location'].unique().tolist())
    loc = col31.selectbox("Select location", loc_codes, key="loc_day_plot")
    chan_codes = st.session_state.channel_df.query('Location == @loc')['Channel'].unique(
    ).tolist()
    chan = col32.selectbox("Select channel", chan_codes)
    # st.session_state['chans'] = st.multiselect("Select channel(s)", chan_codes)
    # chans = st.session_state['chans']

    day = st.date_input('Day', value="default_value_today")
    start_date = datetime.datetime(day.year, day.month, day.day)
    end_date = start_date + datetime.timedelta(hours=24)
    # fmin, fmax = None, None
    # if st.checkbox('Apply filter', help="Applies a linear detrend and a 4th order Butterworth bandpass filter."):
    #    col27, col28 = st.columns(2)
    #    fmin = col27.number_input('Lower Freq. (Hz)', min_value=0, max_value=50, value=0)
    #    fmax = col28.number_input('Higher Freq. (Hz)', min_value=fmin, max_value=50)
    #    # add validity check vs fs


    if "day_traces" not in st.session_state:
        st.session_state.day_traces = None
    if st.button('View day plot', disabled=True if chan is None else False):
        with st.spinner('Fetching traces...'):
            traces = get_trace(net, sta, loc, chan, start_date, end_date)
            if traces is None:
                st.session_state.day_traces = None
                st.stop()
        st.session_state.day_traces = traces
            # if fmin is not None and fmax is not None:
            #    traces.detrend("linear")
            #    traces.filter("bandpass", freqmin=fmin, freqmax=fmax)
        st.session_state.day_traces.detrend("linear")
        st.session_state.day_traces.merge(method=1)
        # add info about these preprocesses 
    if st.session_state.day_traces is not None:
        
        fig = st.session_state.day_traces.plot(handle=True, type='dayplot')
            #traces.filter("bandpass", freqmin=0.5, freqmax=30)
            # fig.axes[-1].set_xlabel('Time')
            # fig.axes[-1].set_ylabel('Counts')

        st.pyplot(fig)
            #fig_html = mpld3.fig_to_html(fig)
            #components.html(fig_html, height=600)
