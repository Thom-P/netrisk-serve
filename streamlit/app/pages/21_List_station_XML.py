import os
from datetime import datetime
import io

import zipfile
import streamlit as st
import pandas as pd

#st.set_page_config(
#    page_title='List station XML files',
#    layout="wide",
#    page_icon=None,
#    initial_sidebar_state="auto",
#    menu_items=None
#)
# st.sidebar.markdown('# Placeholder')

sidebar_logo = "static/netrisk-serve-hr-logo-transparent.png"
main_body_logo = "static/netrisk-serve-icon-transparent.png"
st.logo(sidebar_logo, icon_image=main_body_logo)

st.title('My station XML files')

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


@st.experimental_dialog("Confirmation required")
def delete_files(rows):
    st.write("The following file(s) will be deleted on the server:")
    st.write(', '.join(df['File name'].iloc[rows].tolist()))
    if st.button("Delete"):
        for row in rows:
            os.remove('/data/xml/' + df['File name'].iloc[row])
        st.rerun()

@st.experimental_dialog("Download archive")
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


@st.experimental_dialog("Download XML file")
def download_xml_file(fname):
    with open('/data/xml/' + fname, 'rt') as file:
        st.download_button(
            label=f"Download",
            data=file,
            file_name=fname,
    )

selected_rows = event.selection['rows']
is_disabled = len(selected_rows) == 0

cols = st.columns([1, 1, 6]) # hack to have buttons side by side without big gap
if cols[0].button("Delete selected file(s)", disabled=is_disabled):
    delete_files(selected_rows)

if cols[1].button("Download selected file(s)", disabled=is_disabled):
    if len(selected_rows) > 1:
        download_xml_archive(df['File name'].iloc[selected_rows].tolist())
    else:
        download_xml_file(df['File name'].iloc[selected_rows[0]])