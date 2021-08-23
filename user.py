import streamlit as st
import yfinance as yf
import pandas as pd
import db
from init import init
from cryptocmd import CmcScraper
from streamlit import session_state as state

APP = 'portfolio'
CREDS = 'user_credentials.xlsx'


def logout():
    for i in state.keys():
        del state[i]

def settings():
    st.write('OK')

def user():
    cols = st.columns([3, 1, 1])
    cols[0].write(f'## Welcome, {state.user}')
    cols[1].button('Settings', on_click=settings)
    cols[2].button('Logout', on_click=logout)

    # if logout_button:
        # del state.user
        # st.success('Logged Out')
        # # st.button('OK')

