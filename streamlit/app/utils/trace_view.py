import streamlit as st
import datetime


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

def select_filter_params(loc, chans):
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

