import streamlit as st
import yfinance as yf
import pandas as pd
import db
from cryptocmd import CmcScraper
from streamlit import session_state as state

APP = 'portfolio'
CREDS = 'user_credentials.xlsx'


def login():
    with st.form(key='login'):
        user = st.text_input('User', '')
        password = st.text_input('Password', '', type='password')
        submit_button = st.form_submit_button(label='Login')
    if submit_button:
        if not state.user_credentials.loc[
                (state.user_credentials.user == user) &
                (state.user_credentials.password == password)].empty:
            state.user = user
        else:
            st.warning('Utilizador / Password errados')
            st.stop()


def register():
    with st.form(key='register'):
        user = st.text_input('New Username', '')
        password = st.text_input('Password', '', type='password')
        submit_button = st.form_submit_button(label='Register Account')
    if submit_button:
        if not password:
            st.sidebar.warning('Password field is empty')
            st.stop()
        if any(state.user_credentials.user == user):
            st.warning('Username already registered')
            st.stop()
        else:
            placeholder = st.empty()
            placeholder.warning('Registering  account...')
            state.user_credentials = state.user_credentials.append(
                    {'user': user, 'password': password},
                    ignore_index=True).sort_values(by='user', axis=0)
            dbx = db.get_dropbox_client()
            db.upload_dataframe(
                    dbx, APP, state.user_credentials, CREDS)
            state.user = user
            placeholder.success('Account registered')
            ok = st.button('Ok')
            if ok:
                pass


def about():
    st.write(
            'Compare your Portfolio with your friends '
            'and other users.'
            )
    st.write(
            'You can create a portfolio using Stocks from '
            '[Yahoo Finance](http://www.yahoofinance.com) '
            'or Cryptocurrencies from '
            '[CoinmarketCap](http://www.coinmarketcap.com).')



def main():
    dbx = db.get_dropbox_client()
    if 'user_credentials' not in state:
        try:
            state.user_credentials = db.download_dataframe(dbx, APP, CREDS)
        except Exception:
            st.error('Could not download files from database.')
            st.stop()

    st.title(':racing_car: RACE TO THE TOP :rocket:')

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






if __name__ == '__main__':
    main()


    # if 'df' not in state:
        # state.df = pd.DataFrame(columns=['Type', 'Product', 'Amount'])

    # with st.form(key='search'):
        # product = st.text_input('Search for Product')
        # option = st.radio('Choose one', options=['Stock', 'Crypto'])
        # search = st.form_submit_button(label='Search')

    # if search:
        # if option == 'Stock':
            # try:
                # data = yf.Ticker(product).info['currentPrice']
            # except KeyError:
                # st.warning('Could not find product. Please check spelling')
                # st.stop()
        # else:
            # try:
                # data = CmcScraper(product).get_dataframe().iloc[0].Close
            # except TypeError:
                # st.warning('Could not find product. Please check spelling')
                # st.stop()
        # state.product = product.upper()
        # state.type = option
        # state.value = f'{round(data, 2)} USD'
        # state.valid_product_search = True

    # if 'valid_product_search' in state:
        # with st.form(key='add'):
            # st.write('### Add / Change Portfolio?')
            # col1, col2 = st.columns(2)
            # col1.metric(
                    # label=state.product,
                    # value=state.value,
                    # )
            # amount = col2.text_input('Amount', value='0')
            # add = st.form_submit_button('Add')

        # if add:
            # try:
                # amount = float(amount)
            # except ValueError:
                # st.warning(
                        # 'Could not convert amount to float. '
                        # 'Please check amount'
                        # )
                # st.stop()
            # if amount <= 0:
                # st.warning('You cannot have that amount. Please check amount')
                # st.stop()
            # else:
                # if state.product in state.df.Product.values:
                    # state.df.Amount = state.df.Amount.where(
                            # state.df.Product != state.product, amount)
                # else:
                    # row = {
                            # 'Product': state.product,
                            # 'Type': state.type,
                            # 'Amount': amount,
                            # }
                    # state.df = state.df.append(row, ignore_index=True)

    # st.write(state.df.groupby(['Type', 'Product']).agg({'Amount': 'sum'}))
