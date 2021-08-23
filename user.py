import streamlit as st
import yfinance as yf
import pandas as pd
import db
from init import init_page
from cryptocmd import CmcScraper
from streamlit import session_state as state
from currency_converter import CurrencyConverter
import plotly.graph_objects as go


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


def show_personal():
    st.write('### Your Portfolio')
    df = state.df.loc[
            state.df.User == state.user
            ].drop(['User', 'Currency'], axis=1).reset_index(drop=True)
    if df.empty:
        st.warning('Your Portfolio is empty. Please update it in Settings')
        st.stop()
    c = CurrencyConverter()
    fx_rate = c.convert(1, 'USD')
    cols = st.columns(4)
    col_number = 0
    current_value_list = list()
    for i in zip(df.Type, df.Product, df.Amount):
        if i[0] == 'Crypto':
            data = CmcScraper(i[1]).get_dataframe().iloc[:2]
        else:
            data = yf.Ticker(i[1]).history(
                    period='2d').sort_index(ascending=False)
        today_pct_change = data.Close.pct_change(periods=-1).iloc[0]*100
        today_price = data.iloc[0].Close
        today_value = today_price * i[2] * fx_rate
        current_value_list.append(today_value)
        cols[col_number % 4].metric(
                i[1],
                round(today_price, 2),
                f'{round(today_pct_change, 2)}%',
                )
        col_number += 1
    df['Current Value (EUR)'] = current_value_list
    st.write(df)
    st.metric(
            'Portfolio Value',
            f'{round(df["Current Value (EUR)"].sum(), 2)} EUR',
            )

    df_by_type = df.groupby('Type').agg({'Current Value (EUR)': 'sum'})
    labels = df_by_type.index.values
    values = df_by_type['Current Value (EUR)'].values
    fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
    st.write(fig)

    labels = df.Product.values
    values = df['Current Value (EUR)'].values
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
