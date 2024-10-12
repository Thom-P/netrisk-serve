import datetime
import copy
import io

import streamlit as st

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

def select_filter_params(loc, chans, key):
    # get min fs from all selected channels
    sub_df = st.session_state.channel_df.query('Location == @loc')
    min_fs = sub_df[sub_df['Channel'].isin(chans)]['SampleRate'].min() # should test
    unit = st.radio(
        "Units",
        ["Frequency", "Period"],
        label_visibility="collapsed",
        horizontal = True,
        key=key + '_units'
    )

    col27, col28 = st.columns(2)
    if unit == "Frequency":
        fmin = col27.number_input(
                    'Lower Freq. (Hz)',
                    min_value=0.,
                    max_value=min_fs * 0.45,
                    key=key + '_fmin'
                )
        fmax = col28.number_input(
                    'Higher Freq. (Hz)',
                    min_value=fmin,
                    max_value=min_fs * 0.45,
                    key=key + '_fmax'
                )
    else:
        tmin = col27.number_input(
                    'Lower Period (s)',
                    min_value=1. / (0.45 * min_fs),
                    max_value=100000.,
                    key=key + '_tmin'
        )

        tmax = col28.number_input(
            'Upper Period (s)',
            min_value=tmin,
            max_value=100000.,
            key=key + '_tmax'
        )
        fmax = 1./ tmin
        fmin = 1. / tmax

    # todo: add validity check vs fs
    return fmin, fmax

@st.fragment
def download_trace(net, sta, loc, chans, start_date, end_date, fmin=None, fmax=None):
    file_format = st.radio("Select file format", ["MSEED", "SAC", "SEGY"])
    if file_format == "SAC":
        # should only be one trace, and with gap value filled
        if len(chans) > 1:
            st.info("SAC files can only contain single component data.", icon="ℹ️")
            return
        
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
