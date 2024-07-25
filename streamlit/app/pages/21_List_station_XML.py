import os
from datetime import datetime

import streamlit as st
import pandas as pd

st.set_page_config(
    page_title='List station XML files',
    page_icon=None,
    layout="wide",
    initial_sidebar_state="auto",
    menu_items=None
)
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
    st.write("The following files will be deleted on the server:")
    st.write(', '.join(df['File name'].iloc[rows].tolist()))
    if st.button("Confirm deletion"):
        for row in rows:
            os.remove('/data/xml/' + df['File name'].iloc[row])
        st.rerun()
        #for row in reversed(rows):  # reverse so that delete doesnt change remaining indices
        #    st.write(row)
            #st.toast(row['File name'])
            #del os.remove(row['name'])

selected_rows = event.selection['rows']
#if st.button("Delete selected files", on_click=delete_files, args=[selected_rows], disabled=len(selected_rows) == 0):
if st.button("Delete selected files", disabled=len(selected_rows) == 0):
    delete_files(selected_rows)
    #st.rerun() # needed?
