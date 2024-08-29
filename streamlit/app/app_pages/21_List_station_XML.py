import os
from datetime import datetime
import io

import zipfile
import streamlit as st
import pandas as pd


#st.title('Station XML files')
st.header('Station XML files')

xml_files = []
with os.scandir('/data/xml') as dir_entries:
    for entry in dir_entries:
        info = entry.stat()
        xml_files.append((entry.name, datetime.fromtimestamp(info.st_mtime), info.st_size / 1000.))

df = pd.DataFrame(xml_files, columns=['File name', 'Last modified (UTC)', 'Size (kB)'])
event = st.dataframe(df, hide_index=True, on_select='rerun',
    column_config={
        #'Size': st.column_config.NumberColumn(format="%.4f"),
        'Last modified (UTC)': st.column_config.DatetimeColumn(
                    format="DD MMM YYYY, HH:mm",
                    step=60,
                ),
    })


@st.dialog("Confirmation required")
def delete_files(rows):
    st.write("The following file(s) will be deleted on the server:")
    st.write(', '.join(df['File name'].iloc[rows].tolist()))
    if st.button("Delete"):
        for row in rows:
            os.remove('/data/xml/' + df['File name'].iloc[row])
        if 'stations_txt' in st.session_state:
            del st.session_state['stations_txt']  # to allow update
        if 'df_stations' in st.session_state:
            del st.session_state['df_stations']
        st.rerun()

@st.dialog("Download archive")
def download_xml_archive(files):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, mode='a', compression=zipfile.ZIP_DEFLATED, allowZip64=False) as zip_file:
        for file_name in files:
            zip_file.write('/data/xml/' + file_name)
    st.download_button(
        label=f"Download",
        data=zip_buffer,
        file_name='stationXML_files.zip',
    )


@st.dialog("Download XML file")
def download_xml_file(fname):
    with open('/data/xml/' + fname, 'rt') as file:
        st.download_button(
            label=f"Download",
            data=file,
            file_name=fname,
    )

selected_rows = event.selection['rows']
is_disabled = len(selected_rows) == 0

if xml_files:
    st.info('Tick boxes in the leftmost column to select station files.', icon="ℹ️")

cols = st.columns([1, 1, 1, 5]) # hack to have buttons side by side without big gap
if cols[0].button("Delete file(s)", disabled=is_disabled):
    delete_files(selected_rows)

if cols[1].button("Download file(s)", disabled=is_disabled):
    if len(selected_rows) > 1:
        download_xml_archive(df['File name'].iloc[selected_rows].tolist())
    else:
        download_xml_file(df['File name'].iloc[selected_rows[0]])

if cols[2].button("Create new file"):
    st.switch_page("app_pages/20_Add_station_XML.py")
