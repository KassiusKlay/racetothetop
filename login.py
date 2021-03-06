import streamlit as st
import db
from streamlit import session_state as state
import numpy as np

APP = 'racetothetop'


def check_valid_login():
    if state.login_user not in state.user_credentials.user.values:
        login_page()
        st.warning('Wrong username / password')
        st.stop()
    pass_to_check = state.user_credentials.loc[
            state.user_credentials.user == state.login_user].password.iloc[0]
    if isinstance(pass_to_check, (int, float, np.int64)):
        pass_to_check = str(pass_to_check)
    if pass_to_check == state.login_password:
        state.user = state.login_user
    else:
        login_page()
        st.warning('Wrong username / password')
        st.stop()


def check_valid_register():
    if len(state.register_password) == 0:
        login_page()
        st.warning('Password field is empty')
        st.stop()
    elif any(state.user_credentials.user == state.register_user):
        login_page()
        st.warning('Username already registered')
        st.stop()
    else:
        placeholder = st.empty()
        placeholder.warning('Registering  account...')
        state.user_credentials = state.user_credentials.append({
            'user': state.register_user,
            'password': state.register_password,
            }, ignore_index=True).sort_values(by='user', axis=0)
        dbx = db.get_dropbox_client()
        db.upload_dataframe(
                dbx, APP, state.user_credentials, 'user_credentials.xlsx')
        state.user = state.register_user
        placeholder.success('Account registered')
        placeholder.empty()


def login():
    with st.form(key='login'):
        st.text_input('User', '', key='login_user')
        st.text_input(
                'Password', '', type='password', key='login_password')
        st.form_submit_button(
                label='Login', on_click=check_valid_login)


def register():
    with st.form(key='register'):
        st.text_input('New Username', '', key='register_user')
        st.text_input('Password', '', type='password', key='register_password')
        st.form_submit_button(
                label='Register Account', on_click=check_valid_register)


def about():
    st.write(
            'Compare your Portfolio with your friends '
            'and other users.'
            )
    st.write(
            'You can create a portfolio using Stocks* from '
            '[Yahoo Finance](http://www.yahoofinance.com) '
            'or Cryptocurrencies from '
            '[CoinmarketCap](http://www.coinmarketcap.com).')
    st.write(
            'The portfolio is updated only **ONCE** a day, '
            'so you will only see your updated portfolio value '
            'the following day!'
            )
    st.write(
            ' *from the US only'
            )


def login_page():
    cols = st.columns(3)
    login_button = cols[0].button('Login')
    register_button = cols[1].button('Register')
    about_button = cols[2].button('About')

    if login_button:
        state.init = 'login'
    elif register_button:
        state.init = 'register'
    elif about_button:
        state.init = 'about'

    if 'init' in state:
        if state.init == 'login':
            login()
        elif state.init == 'register':
            register()
        else:
            about()
