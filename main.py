import streamlit as st
import yfinance as yf
from pandas_datareader import data as pdr
import db
from cryptocmd import CmcScraper
from streamlit import session_state as state
import plotly.express as px
import datetime


APP = 'racetothetop'


def logout():
    for i in state.keys():
        del state[i]


def edit_button():
    state.edit_button = True


def back_edit_buttton():
    del state.edit_button


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


def edit_page():
    st.write(state.df.loc[state.df.User == state.user].drop('User', axis=1))
    st.write('## Add / Edit Product')
    with st.form(key='search'):
        product = st.text_input('Search for Product').upper()
        option = st.radio('Choose one', options=['Stock', 'Crypto'])
        search = st.form_submit_button(label='Search')

    if search:
        if option == 'Stock':
            data = yf.Ticker(product).info
            if 'quoteType' in data.keys():
                if data['quoteType'] == 'EQUITY':
                    state.value = data['currentPrice']
                elif data['quoteType'] == 'ETF':
                    state.value = data['regularMarketPrice']
                else:
                    st.warning(f'Type not recognized: {data["quoteType"]}')
                    st.stop()
                state.currency = data['currency']
            else:
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


def portfolio_page():
    st.write('### Your Portfolio')

    df = state.current_value_df.loc[
            state.current_value_df.User == state.user] .drop(
            ['User', 'Currency'], axis=1)

    if df.empty:
        st.warning('Your Portfolio is empty')
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


def portfolio_checker():
    st.write("# Peep your opponent's portfolio! 👀")
    user = st.selectbox('Select user', state.df.User.unique())
    draw_pie_graphs(user)


def general_user_data():
    pass


def game_page():
    st.write('# Who is the boss? 👑 Who sucks? 🤮 ')
    df = state.time_df.copy()
    pct_df = df.groupby('User').Value.pct_change()
    df['Percentage'] = pct_df
    daily_winner_index = df.loc[
            df.Date.dt.date == datetime.date.today()].Percentage.idxmax()
    daily_looser_index = df.loc[
            df.Date.dt.date == datetime.date.today()].Percentage.idxmin()
    cols = st.columns(2)
    cols[0].metric(
            'Daily Winner',
            df.iloc[daily_winner_index].User,
            f'{round(df.iloc[daily_winner_index].Percentage*100, 2)}%',
            )
    if daily_looser_index != daily_winner_index:
        cols[1].metric(
                'Daily Looser',
                df.iloc[daily_looser_index].User,
                f'{round(df.iloc[daily_looser_index].Percentage*100, 2)}%',
                )
    st.markdown('---')

    portfolio_checker()
    st.markdown('---')

    general_user_data()

    st.markdown('''

    ## To Do:

    - Weekly, Monthy and Yearly Winner and Loser
    - General User Data
    ''')


def main_page():
    if 'main_page' not in state:
        state.main_page = 'game'
    st.markdown(f'## Welcome, {state.user}')
    cols = st.columns(4)
    game_button = cols[0].button('Game')
    portfolio_button = cols[1].button('Your Portfolio')
    edit_button = cols[2].button('Edit Portfolio')
    cols[3].button('Logout', on_click=logout)
    st.markdown('---')

    if game_button:
        state.main_page = 'game'
    elif portfolio_button:
        state.main_page = 'portfolio'
    elif edit_button:
        state.main_page = 'edit'

    if state.main_page == 'game':
        game_page()
    elif state.main_page == 'portfolio':
        portfolio_page()
    elif state.main_page == 'edit':
        edit_page()
