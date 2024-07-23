import streamlit as st

st.set_page_config(
    page_title='Station FTP accounts',
    page_icon=None, layout="wide",
    initial_sidebar_state="auto",
    menu_items=None
)
# st.sidebar.markdown('Stations and traces')

sidebar_logo = "static/netrisk-serve-hr-logo-transparent.png"
main_body_logo = "static/netrisk-serve-icon-transparent.png"
st.logo(sidebar_logo, icon_image=main_body_logo)

#st.markdown('## Stations and traces')
st.title('Station FTP accounts')
