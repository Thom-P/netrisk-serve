import streamlit as st
import folium
from streamlit_dimensions import st_dimensions

def create_map():
    map_center = st.session_state.df_stations[['Latitude', 'Longitude']].mean(
        ).values.tolist()
    m = folium.Map(map_center)  # create map centered on network
    for _, row in st.session_state.df_stations.iterrows():
        info = row['Network'] + ' ' + row['Station'] + '\n' + row['SiteName']
        #icon = get_icon_div(row['Station'])
        folium.Marker(
            [row['Latitude'], row['Longitude']],
            #icon=icon,
            icon=folium.Icon(color='darkblue', prefix='fa',icon='rss'),
            popup=info,
            tooltip='.'.join((row['Network'],row['Station']))
            ).add_to(m)
    sw = st.session_state.df_stations[['Latitude', 'Longitude']].min().values.tolist()
    ne = st.session_state.df_stations[['Latitude', 'Longitude']].max().values.tolist()
    m.fit_bounds([sw, ne]) # interferes with width...
    # keys = ('Network', 'Station', 'Latitude', 'Longitude', 'Elevation', 'SiteName', 'StartTime', 'EndTime')
    # m = folium.Map(location=(stations[0]['Latitude'], stations[0]['Longitude']), tiles='OpenTopoMap')
    # to add text, see https://github.com/python-visualization/folium/issues/340
    return m

def get_icon_div(label):
    div = folium.DivIcon(html=(
        '<svg height="50" width="50">'
        '<polygon points="5,5 45,5 25,45" fill="red" stroke="black" />'
        '<text x="11" y="15" font-size="10px" font-weight="bold"'
        'fill="black">' + label + '</text>' # need to sanitize label?
        '</svg>'
    ))
    return div

@st.fragment
def get_map_col_width():
    width=st_dimensions(key="map_col")
    return width

