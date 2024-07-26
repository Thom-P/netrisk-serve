import streamlit as st
import pandas as pd
import berkeleydb.db as db

#st.set_page_config(
#    page_title='Station FTP accounts',
#    page_icon=None, layout="wide",
#    initial_sidebar_state="auto",
#    menu_items=None
#)
# st.sidebar.markdown('Stations and traces')

#sidebar_logo = "static/netrisk-serve-hr-logo-transparent.png"
#main_body_logo = "static/netrisk-serve-icon-transparent.png"
#st.logo(sidebar_logo, icon_image=main_body_logo)

#st.markdown('## Stations and traces')
st.title('Station FTP accounts')

user_db = db.DB()
user_db.open('/data/ftp_users/vusers.db')

users = user_db.items()

df = pd.DataFrame(users, columns=('Login', 'Password'), dtype=str)
st.dataframe(data=df, hide_index=True)
