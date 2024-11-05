import io

import streamlit as st
import pandas as pd
import plotly.express as px

from utils.data_fetch import fetch_channels, fetch_availability


def display_channels(net, sta):
    st.markdown(f'{net} - {sta}')
    channel_data = fetch_channels(net, sta)
    if channel_data is None:
        st.warning('No channel found', icon="⚠️")
        return

    # Channel dataframe
    st.session_state.channel_df = pd.read_csv(
        io.StringIO(channel_data[1:]),
        sep='|',
        dtype={'Location': str}
    )  # remove first char '#' (header line included as comment)

    st.dataframe(
        st.session_state.channel_df,
        hide_index=True,
        key="channel_data",
    )
    return


def display_availabilty(net, sta):
    st.markdown(f'{net} - {sta}')
    avail_data = fetch_availability(net, sta)
    if avail_data is None:
        st.warning('Data availability information not found', icon="⚠️")
        return
    # Availability dataframe
    avail_df = pd.read_csv(
        io.StringIO(avail_data[1:]),
        sep=r'\s+',
        dtype=str,
        parse_dates=['Earliest', 'Latest'],
        # date_format="ISO8601"
    )  # remove first char '#' (header line included as comment)
    # st.dataframe(avail_df)
    avail_df.rename(columns={"C": "Channel", "Earliest": "Trace Start",
                             "Latest": "Trace End"}, inplace=True)

    # need to simplify todo
    avail_df['Trace Start'] = pd.to_datetime(avail_df['Trace Start'],
                                             format='mixed')
    avail_df['Trace End'] = pd.to_datetime(avail_df['Trace End'],
                                           format='mixed')

    # gaps: add new coloumn
    avail_df['Gap End'] = avail_df.groupby('Channel')['Trace Start'].shift(
        -1, fill_value=pd.NaT
    )

    # add quality and samplerate in hover?
    try:
        fig = px.timeline(avail_df[['Channel', 'Trace Start', 'Trace End']],
                          x_start="Trace Start", x_end="Trace End",
                          y="Channel")  # use channel code as task name
        fig.update_traces(name='Data', showlegend=True)

        fig_gaps = px.timeline(avail_df, x_start='Trace End', x_end='Gap End',
                               y='Channel')  # could use color for quality
        fig_gaps.update_traces(marker=dict(color='red'), width=0.5,
                               name='Gaps', showlegend=True)
        fig.add_trace(fig_gaps.data[0])

        fig.update_yaxes(autorange="reversed", title_text="Channel",
                         title_font={'size': 18}, tickfont={'size': 16},
                         ticklabelstandoff=10)  # otherwise listed bottom up
        fig.update_xaxes(title_text='Date', title_font={'size': 18},
                         tickfont={'size': 16}, showgrid=True,
                         gridcolor='white', gridwidth=1)
        fig.update_layout(plot_bgcolor='rgb(240, 240, 240)')
        st.plotly_chart(fig, use_container_width=True)
        st.info('Data availability is updated every hour', icon="ℹ️")
    except Exception as err:
        st.error(err)
        return
    return
