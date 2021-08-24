import streamlit as st
import yfinance as yf
import pandas as pd
import db
from cryptocmd import CmcScraper
from streamlit import session_state as state
from currency_converter import CurrencyConverter
import plotly.graph_objects as go
import concurrent.futures
import numpy as np


APP = 'portfolio'


def logout():
    for i in state.keys():
        del state[i]


def settings_button():
    state.settings_button = True


def back_settings_buttton():
    del state.settings_button


def edit_portfolio():
    if state.amount == 0:
        state.df = state.df.loc[~(
            (state.df.User == state.user) &
            (state.df.Product == state.product))]
    elif state.product in state.df.loc[
            state.df.User == state.user].Product.values:
        state.df.Amount = state.df.Amount.where(
                (state.df.Product != state.product) |
                (state.df.User != state.user), state.amount)
    else:
        row = {
                'User': state.user,
                'Type': state.option,
                'Product': state.product,
                'Currency': state.currency,
                'Amount': state.amount,
                }
        state.df = state.df.append(row, ignore_index=True).sort_values(
                ['User', 'Type', 'Product'])
    dbx = db.get_dropbox_client()
    db.upload_dataframe(dbx, APP, state.df, 'df.xlsx')
    for i in ['product', 'option', 'value', 'currency', 'amount']:
        del state[i]


def settings_page():
    st.write(state.df.loc[state.df.User == state.user])
    st.write('## Add / Edit Product')
    with st.form(key='search'):
        product = st.text_input('Search for Product').upper()
        option = st.radio('Choose one', options=['Stock', 'Crypto'])
        search = st.form_submit_button(label='Search')

    if search:
        if option == 'Stock':
            data = yf.Ticker(product).info
            try:
                state.value = round(data['currentPrice'], 2)
                state.currency = data['currency']
            except KeyError:
                st.warning('Could not find product. Please check spelling')
                st.stop()
        else:
            try:
                state.value = round(
                        CmcScraper(product).get_dataframe().iloc[0].Close, 2)
                state.currency = 'USD'
            except TypeError:
                st.warning('Could not find product. Please check spelling')
                st.stop()
        state.product = product
        state.option = option

    if 'product' in state:
        st.metric(state.product, f'{state.value} {state.currency}')
        state.amount = st.text_input(
                f'How many {state.product} you currently own?')
        if len(state.amount) > 0:
            try:
                state.amount = float(state.amount)
                assert state.amount >= 0
            except Exception:
                st.warning('Amount not a valid number')
            else:
                st.button('Confirm', on_click=edit_portfolio)


def get_product_data(i):
    if i[0] == 'Crypto':
        data = CmcScraper(i[1]).get_dataframe().iloc[:2]
    else:
        data = yf.Ticker(i[1]).history(
                period='2d').sort_index(ascending=False)
    return data


def get_daily_df(user):
    c = CurrencyConverter()
    fx_rate = c.convert(1, 'USD')

    df = state.df.loc[
            state.df.User == user
            ].drop(['User', 'Currency'], axis=1).reset_index(drop=True)

    if df.empty:
        st.warning('Your Portfolio is empty. Please update it in Settings')
        st.stop()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(get_product_data, zip(df.Type, df.Product))

    df[['Price', 'Change', 'Value']] = np.nan
    for i, data in enumerate(results):
        today_price = data.iloc[0].Close
        today_pct_change = data.Close.pct_change(periods=-1).iloc[0]*100
        today_value = today_price * df.iloc[i].Amount * fx_rate
        df.iat[i, 3] = today_price
        df.iat[i, 4] = today_pct_change
        df.iat[i, 5] = today_value
    return df


def show_personal():
    st.write('### Your Portfolio')
    df = state.df.loc[state.df.User == state.user].drop(
            ['User', 'Currency'], axis=1)
    df = pd.merge(df, state.products_df)
    c = CurrencyConverter()
    fx_rate = c.convert(1, 'USD')
    df['Value'] = df.Amount * df.Price * fx_rate
    cols = st.columns(4)
    col_number = 0
    for i in range(len(df)):
        cols[col_number % 4].metric(
                df.iloc[i].Product,
                f'{round(df.iloc[i]["Price"], 2)}',
                f'{round(df.iloc[i]["Change"], 2)}%',
                )
        col_number += 1
    st.write(df)
    st.metric(
            'Portfolio Value',
            f'{round(df["Value"].sum(), 2)} EUR',
            )
    df_by_type = df.groupby('Type').agg({'Value': 'sum'})
    labels = df_by_type.index.values
    values = df_by_type['Value'].values
    fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
    st.write(fig)

    labels = df.Product.values
    values = df['Value'].values
    fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
    st.write(fig)


def user_page():
    cols = st.columns([3, 1, 1])
    cols[0].write(f'## Welcome, {state.user}')
    cols[1].button('Settings', on_click=settings_button)
    cols[2].button('Logout', on_click=logout)

    if 'settings_button' in state:
        settings_page()
        st.button('Back', on_click=back_settings_buttton)
    else:
        # show_overall()
        show_personal()
