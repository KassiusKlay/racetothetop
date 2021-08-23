import streamlit as st
import pandas as pd
import db
from init import init_page
from user import user_page
from streamlit import session_state as state

APP = 'portfolio'
CREDS = 'user_credentials.xlsx'
DF = 'df.xlsx'


def main():
    dbx = db.get_dropbox_client()
    if 'user_credentials' not in state:
        try:
            state.user_credentials = db.download_dataframe(dbx, APP, CREDS)
            state.df = db.download_dataframe(dbx, APP, DF)
        except Exception:
            st.error('Could not download files from database.')
            st.stop()

    if 'user' not in state:
        init_page()
    else:
        user_page()


if __name__ == '__main__':
    main()
