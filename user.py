import streamlit as st
import yfinance as yf
import pandas as pd
import db
from cryptocmd import CmcScraper
from streamlit import session_state as state
from currency_converter import CurrencyConverter
import plotly.express as px
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


def draw_pie_graphs(user):
    df = state.current_value_df.loc[
            state.current_value_df.User == user] .drop(
            ['User', 'Currency'], axis=1)
    df['Percentage'] = df.Value / df.Value.sum() * 100
    df.loc[df['Percentage'] < 1, 'Product'] = 'Other Products'
    fig = px.pie(
            df,
            values='Percentage',
            names=df.Product,
            title='Percentage by Product',
            )
    st.write(fig)
    df = df.groupby('Type').agg({'Value': 'sum'})
    df['Percentage'] = df.Value / df.Value.sum() * 100
    fig = px.pie(
            df,
            values='Percentage',
            names=df.index,
            title='Percentage by Type',
            )
    st.write(fig)


def draw_line_graph(user):
    df = state.time_df.loc[state.time_df.User == user]
    fig = px.line(df, x='Date', y="Value")
    st.write(fig)


def show_personal():
    st.write('### Your Portfolio')

    df = state.current_value_df.loc[
            state.current_value_df.User == state.user] .drop(
            ['User', 'Currency'], axis=1)

    if df.empty:
        st.warning('Your Portfolio is empty. Please update it in Settings')
        st.stop()

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
    st.metric('Portfolio Value', f'{round(df["Value"].sum(), 2)} EUR')
    draw_line_graph(state.user)
    draw_pie_graphs(state.user)


def user_page():
    cols = st.columns([3, 1, 1])
    cols[0].write(f'## Welcome, {state.user}')
    cols[1].button('Settings', on_click=settings_button)
    cols[2].button('Logout', on_click=logout)

    if 'settings_button' in state:
        st.button('Back', on_click=back_settings_buttton)
        settings_page()
    else:
        # show_overall()
        show_personal()
