import requests
import io
import datetime
import math
import copy

import streamlit as st
import streamlit.components.v1 as components
import folium
import pandas as pd
import mpld3
from streamlit_folium import st_folium
from streamlit_dimensions import st_dimensions
# from obspy import read
from obspy.clients.fdsn import Client
from obspy.core import UTCDateTime
from obspy.clients.fdsn.header import FDSNNoDataException
import matplotlib.pyplot as plt
import numpy as np

#st.title('Stations and traces')
st.header('Stations and traces')

client = Client("http://seiscomp:8080")  # todo connection test here

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


#@st.cache_data(show_spinner=False)
def get_trace(net, sta, loc, chans, start_date, end_date):
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


def get_icon_div(label):
    div = folium.DivIcon(html=(
        '<svg height="50" width="50">'
        '<polygon points="5,5 45,5 25,45" fill="red" stroke="black" />'
        '<text x="11" y="15" font-size="10px" font-weight="bold"'
        'fill="black">' + label + '</text>' # need to sanitize label?
        '</svg>'
    ))
    return div

if "df_stations" not in st.session_state:
    stations_txt = fetch_stations()
    if stations_txt is None:
        st.info("You first need to create a station XML file and an FTP account for each of your stations.", icon="ℹ️")
        st.stop()
    resp_types = {'Network': str, 'Station': str, 'SiteName': str} # to prevent auto conversion to int when num only names
    st.session_state.df_stations = pd.read_csv(io.StringIO(stations_txt[1:]), sep='|', dtype=resp_types)
    # remove first char '#' (header line included as comment)

inv = client.get_stations(level="station")  # can cache ? combine with previous fetch ?
net_codes = {net.code: ind for ind, net in enumerate(inv.networks)}  # need to test if empty

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
map_center = st.session_state.df_stations[['Latitude', 'Longitude']].mean(
    ).values.tolist()
m = folium.Map(map_center)  # create map centered on network
for _, row in st.session_state.df_stations.iterrows():
    info = row['Network'] + ' ' + row['Station'] + '\n' + row['SiteName']
    icon = get_icon_div(row['Station'])
    folium.Marker(
        [row['Latitude'], row['Longitude']],
        icon=icon,
        popup=info,
        tooltip='.'.join((row['Network'],row['Station']))
        ).add_to(m)
sw = st.session_state.df_stations[['Latitude', 'Longitude']].min().values.tolist()
ne = st.session_state.df_stations[['Latitude', 'Longitude']].max().values.tolist()
m.fit_bounds([sw, ne]) # interferes with width...
# keys = ('Network', 'Station', 'Latitude', 'Longitude', 'Elevation', 'SiteName', 'StartTime', 'EndTime')
# m = folium.Map(location=(stations[0]['Latitude'], stations[0]['Longitude']), tiles='OpenTopoMap')
# to add text, see https://github.com/python-visualization/folium/issues/340

##########################

col1, col2 = st.columns([0.6, 0.4])
# call to render Folium map in Streamlit, but don't get any data back
# from the map (so that it won't rerun the app when the user interacts)
with col2:
    st.text("") # hack for pseudo alignment of map
    #st.text("")
    #map_data = st_folium(m, width=800, returned_objects=[])
    map_data = st_folium(m, width=st_dimensions(key="map_col"), returned_objects=[])

    # width of container should be checked using add-on
    # (https://github.com/avsolatorio/streamlit-dimensions), other wise messes
    # with bounding box when doesnt fit on screen
    # disabled interactivity because absence of on_click callable makes synchro
    # with df very convoluted (could try with updating keys to refresh map
    # select and df select)

tab1, tab2, tab3 = col1.tabs(["Station info", "Trace", "Day plot"])

with tab2:
    c = st.empty()
    c.write('Select a station in the previous tab.')

# station info
with tab1:
    event = st.dataframe(
        st.session_state.df_stations,
        hide_index=True,
        key=None,
        on_select="rerun",
        selection_mode="single-row",
    )

    with st.expander("## Channels:"):
        # Station selection in dataframe
        channel_data = None
        row_index = event.selection['rows']
        # st.markdown('## Channels')
        if not row_index:
            st.markdown(
                'Select station by ticking box in the leftmost column.'
                )
            st.stop()

        net, sta = st.session_state.df_stations.iloc[row_index[0]][['Network', 'Station']]
        channel_data = fetch_channels(net, sta)

        if channel_data is None:
            st.stop()

        # Channel dataframe
        channel_df = pd.read_csv(
            io.StringIO(channel_data[1:]),
            sep='|',
            dtype={'Location': str}
        )  # remove first char '#' (header line included as comment)
        st.dataframe(
            channel_df,
            hide_index=True,
            key="channel_data",
        )
    with st.expander('## Todo: graph of data availability'):
        st.write('todo')

# Trace
with tab2:
    c.markdown(f'## {net}.{sta}')
    # if channel_data is None: # doesnt work as exec was stopped in prev tab
    #    st.write('Select a station in the previous tab.')
    #    st.stop()

    col21, col22 = st.columns(2)
    loc_codes = sorted(channel_df['Location'].unique().tolist())
    loc = col21.selectbox("Select location", loc_codes) # add 2 digit format
    sub_df = channel_df.query('Location == @loc')
    chan_codes = sub_df['Channel'].unique().tolist()
    chans = col22.multiselect("Select channel(s)", chan_codes)

    col23, col24, col25, col26 = st.columns(4)
    start_day = col23.date_input('Start Date', value="default_value_today")
    start_time = col24.time_input(
        'Start Time',
        value=datetime.time(0, 0),
        step=3600
    )
    end_day = col25.date_input(
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
    end_time = col26.time_input(
        'End Time',
        value=datetime.time(0, 0),
        step=3600
    )

    start_date = datetime.datetime.combine(start_day, start_time)
    end_date = datetime.datetime.combine(end_day, end_time)

    fmin, fmax = None, None
    filt_msg = "Applies a linear detrend and a 4th order" \
        "Butterworth bandpass filter."
    if st.checkbox('Apply filter', help=filt_msg):
        # get min fs from all selected channels
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

    # add validity check vs fs
    
    resp_msg = "Todo: help message here" \
        "More here."
    resp_remove = st.checkbox('Remove instrument response', help=resp_msg)
    #fig_deconv = plt.figure()
    #resp_plot_buffer = io.BytesIO()
    
    if "traces" not in st.session_state:
        st.session_state.traces = None
    if st.button('View Trace', disabled=False if chans else True):
        with st.spinner('Fetching traces...'):
            traces = get_trace(
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
                    traces.remove_response(output='DEF', water_level=60, pre_filt=None, zero_mean=True, taper=True, taper_fraction=0.05, plot=False, fig=None)
                    # plot bugs
                    #traces.remove_response(output='DEF', water_level=60, pre_filt=None, zero_mean=True, taper=True, taper_fraction=0.05, plot=True, fig=fig_deconv)
                except Exception as err:
                    st.error(err, icon="🚨")
                    st.stop()
        st.session_state.traces = traces

    if st.session_state.traces is not None:

            #fig = plt.figure()
            #traces.plot(fig=fig) # todo: add size to stretch to container size
            #fig.axes[-1].set_xlabel('Time')
            #fig.axes[-1].set_ylabel('Counts')
            # This below causes logic issue (radio button not showing in fragment, why?)
            #fig_html = mpld3.fig_to_html(fig)
            #components.html(fig_html, height=600)

            # fig is non-interactive with this approach
            # issue seems to happen when plot is bigger than container size...
            #fig = traces.plot(handle=True)

            #fig = plt.figure()
            #traces.plot(fig=fig) # todo: add size to stretch to container size
            #fig = traces.plot(handle=True, size=(800, 250))

        fig = st.session_state.traces.plot(handle=True)
        fig.axes[-1].set_xlabel('Time')
        fig.axes[-1].set_ylabel('Counts')
            #st.pyplot(fig, use_container_width=False)
        st.pyplot(fig)

            # approach below freezes on large traces
            # (obspy uses special minmax method for large traces)
            # fig, ax = plt.subplots()
            # tr = traces[0]
            # ax.plot(tr.times("matplotlib"), tr.data, "k-")
            # ax.xaxis_date()
            # fig.autofmt_xdate()
            # ax.set_xlabel('Time')
            # ax.set_ylabel('Counts')
        
        #with st.expander("Visualize response removal steps"):
        #    with st.spinner('Loading plot...'):
        #        st.pyplot(fig_deconv)
        #        #st.image(resp_plot_buffer, use_column_width=True)


        @st.fragment
        def download_trace():
            file_format = st.radio("Select file format", ["MSEED", "SAC", "SEGY"])
            if file_format == "SAC":
                # should only be one trace
                if len(chans) > 1:
                    st.info("SAC files can only contain single component data.", icon="ℹ️")
                    st.stop()
                trace_merged = copy.deepcopy(st.session_state.traces)
                trace_merged.merge(method=1) # in place op, method use most recent value when overlap
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
            elif file_format == "SEGY":
                try:
                    st.session_state.traces.write(file_buff, format=file_format) 
                except Exception as err:
                    st.error(f"{err}", icon="🚨")
                    st.stop()
                #raise

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


# import plotly.express as px
# im = np.random.random((200, 200))
# labels = {
#        'x':"X Axis Title",
#        'y':"X Axis Title" ,
#        'color':'Z Label'
#        }
# fig = px.imshow(im,aspect='equal',labels = labels)
# fig = px.imshow(im, labels = labels)
# st.plotly_chart(fig)


########### Day plot
with tab3:  # need indep vars?
    # need to cleanup widget duplications
    c.markdown(f'## {net}.{sta}')
    col31, col32 = st.columns(2)
    loc_codes = sorted(channel_df['Location'].unique().tolist())
    loc = col31.selectbox("Select loc", loc_codes) # add 2 digit formatting
    chan_codes = channel_df.query('Location == @loc')['Channel'].unique(
    ).tolist()
    chan = col32.selectbox("Select chan", chan_codes)
    # st.session_state['chans'] = st.multiselect("Select channel(s)", chan_codes)
    # chans = st.session_state['chans']

    day = st.date_input('Day', value="default_value_today")

    # fmin, fmax = None, None
    # if st.checkbox('Apply filter', help="Applies a linear detrend and a 4th order Butterworth bandpass filter."):
    #    col27, col28 = st.columns(2)
    #    fmin = col27.number_input('Lower Freq. (Hz)', min_value=0, max_value=50, value=0)
    #    fmax = col28.number_input('Higher Freq. (Hz)', min_value=fmin, max_value=50)
    #    # add validity check vs fs


# if st.button('View day plot', disabled=True if chan is None else False):
#     with st.spinner('Loading...'):
#         traces = get_trace(net, sta, loc, chan)
#         if traces is None:
#             st.stop()
#         # if fmin is not None and fmax is not None:
#         #    traces.detrend("linear")
#         #    traces.filter("bandpass", freqmin=fmin, freqmax=fmax)
#         fig = plt.figure()
#         traces.detrend("linear")
#         traces.filter("bandpass", freqmin=0.5, freqmax=30)
#         traces.plot(fig=fig, type='dayplot') # todo: add size to stretch to container size
#         # fig.axes[-1].set_xlabel('Time')
#         # fig.axes[-1].set_ylabel('Counts')

#         fig_html = mpld3.fig_to_html(fig)
#         components.html(fig_html, height=600)
