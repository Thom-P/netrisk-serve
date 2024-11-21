"""Page to manage the FTP accounts of the netrisk stations.

Display a list of all FTP accounts. Allow to create and delete accounts.
The accounts are stored in a BerkeleyDB database on the server. They are
needed for authentication before upload of the raw seismic data.
"""
import os
from pathlib import Path

import streamlit as st
import pandas as pd
import berkeleydb
from passlib.hash import sha512_crypt

from utils.dataframe import dataframe_with_selections


st.header('Station FTP accounts')

if 'user_db' not in st.session_state:
    user_db = berkeleydb.db.DB()
    user_db.open('/data/ftp_users/vsftpd-virtual-user.db')
    st.session_state['user_db'] = user_db
users = st.session_state.user_db.items()

# Create and display the user (account) table
df = pd.DataFrame(users, columns=('Login', 'Password hash'),  dtype=str)
selection = dataframe_with_selections(df)


@st.dialog("Confirmation required")
def delete_accounts(rows):
    """Delete the selected FTP accounts from the server upon confirmation."""
    st.write("The following account(s) will be deleted on the server:")
    st.write(', '.join(df['Login'].iloc[rows].tolist()))
    if st.button("Delete", key='confirm_delete_accounts'):
        for row in rows:
            st.session_state.user_db.delete(
                df['Login'].iloc[row].encode('utf-8')
            )
            st.session_state.user_db.sync()
        st.rerun()


@st.dialog("New FTP account creation")
def create_account():
    """Create a new FTP account on the server.

    Prompt the user for a login and password. The login must be unique and
    have at least 4 characters. The password must have at least 6 characters.
    Use SHA-512 to encrypt the password. Add the login and password hash to
    the BerkeleyDB database. Create a directory for the new station data.
    Touch the RELOAD file to trigger the incron daemon to reload its table
    (and watch the newly created directory).
    """
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
    if st.button("Create", key='confirm_create_ftp_account'):
        password_hash = sha512_crypt.hash(password)
        st.session_state.user_db.put(login.encode('utf-8'),
                                     password_hash.encode('utf-8'))
        st.session_state.user_db.sync()
        os.mkdir(f"/data/ftp/{login}")
        # todo add char validation and verif if already exists
        os.chmod(f"/data/ftp/{login}", 0o777)
        # need exec permission to write files into
        # (could create vsftpd user in streamlit dockerfile as well instead)
        Path('/data/reload/RELOAD').touch()
        # does not work reliably, need to check why
        st.rerun()


selected_rows = selection['selected_rows_indices']
is_disabled = len(selected_rows) == 0

# Hack to have buttons side by side without big gap
cols = st.columns([1, 1, 5])
if cols[0].button("Delete", key='delete_ftp_accounts', disabled=is_disabled):
    delete_accounts(selected_rows)

if cols[1].button("Create new", key='create_ftp_account'):
    create_account()
