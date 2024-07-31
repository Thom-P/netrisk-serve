import streamlit as st
import pandas as pd
import berkeleydb.db as db


st.title('Station FTP accounts')

if 'user_db' not in st.session_state:
    user_db = db.DB()
    user_db.open('/data/ftp_users/vusers.db')
    st.session_state['user_db'] = user_db
users = st.session_state.user_db.items()

df = pd.DataFrame(users, columns=('Login', 'Password'), dtype=str)
event = st.dataframe(data=df, hide_index=True, on_select='rerun')

@st.dialog("Confirmation required")
def delete_accounts(rows):
    st.write("The following account(s) will be deleted on the server:")
    st.write(', '.join(df['Login'].iloc[rows].tolist()))
    if st.button("Delete"):
        for row in rows:
            st.session_state.user_db.delete(df['Login'].iloc[row].encode('utf-8'))
            st.session_state.user_db.sync()
            #db remove
        st.rerun()

@st.dialog("New FTP account creation")
def create_account():
    login = st.text_input("Login:", max_chars=32)
    if len(login) < 4:
        st.warning("Logins should have at least 4 characters")
        st.stop()
    if st.session_state.user_db.exists(login.encode('utf-8')):
        st.error("This login already exists.")
        st.stop()
    password = st.text_input("Password:", type='password')
    if len(password) < 6:
        st.warning("Passwords should have at least 6 characters")
        st.stop()
    if st.button("Create"):
        st.session_state.user_db.put(login.encode('utf-8'), password.encode('utf-8'))
        st.session_state.user_db.sync()
        st.rerun()

selected_rows = event.selection['rows']
is_disabled = len(selected_rows) == 0

cols = st.columns([1, 1, 6]) # hack to have buttons side by side without big gap
if cols[0].button("Delete selected account(s)", disabled=is_disabled):
    delete_accounts(selected_rows)

if cols[1].button("Create new account"):
    create_account()
