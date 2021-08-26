import streamlit as st
import pandas as pd
import db
from login import login_page
from main import main_page
from streamlit import session_state as state
import concurrent.futures
import numpy as np
from currency_converter import CurrencyConverter
import datetime
from cryptocmd import CmcScraper
import yfinance as yf

APP = 'racetothetop'


def get_product_data(i):
    if i[0] == 'Crypto':
        data = CmcScraper(i[1]).get_dataframe().iloc[:2]
    else:
        data = yf.Ticker(i[1]).history(
                period='2d').sort_index(ascending=False)
    return data


def get_all_products_daily_price_and_pct_change():
    df = state.df[['Type', 'Product']].drop_duplicates()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(get_product_data, zip(df.Type, df.Product))

    df[['Price', 'Change']] = np.nan
    for i, data in enumerate(results):
        today_price = data.iloc[0].Close
        today_pct_change = data.Close.pct_change(periods=-1).iloc[0]*100
        df.iat[i, 2] = today_price
        df.iat[i, 3] = today_pct_change
    return df


def get_current_value_df():
    c = CurrencyConverter()
    fx_rate = c.convert(1, 'USD')
    df = pd.merge(state.df, state.products_df)
    c = CurrencyConverter()
    fx_rate = c.convert(1, 'USD')
    df['Value'] = df.Amount * df.Price * fx_rate
    return df


def update_time_df():
    df = state.current_value_df.groupby('User').agg(
            {'Value': 'sum'}).reset_index()
    df['Date'] = datetime.date.today()
    state.time_df = pd.concat([state.time_df, df])
    dbx = db.get_dropbox_client()
    db.upload_dataframe(dbx, APP, state.time_df, 'time_df.xlsx')


def main():
    # st.set_page_config(layout="wide")
    st.title(':racing_car: RACE TO THE TOP :rocket:')
    st.subheader('Think you are a good investor? Think again!')
    st.markdown("""---""")

    dbx = db.get_dropbox_client()
    if 'user_credentials' not in state:
        try:
            state.user_credentials = db.download_dataframe(
                    dbx, APP, 'user_credentials.xlsx')
            state.df = db.download_dataframe(dbx, APP, 'df.xlsx')
            state.time_df = db.download_dataframe(dbx, APP, 'time_df.xlsx')
        except Exception:
            st.error('Could not download files from database.')
            st.stop()

    if 'product_df' not in state:
        try:
            state.products_df = get_all_products_daily_price_and_pct_change()
            state.current_value_df = get_current_value_df()
        except Exception:
            st.error('Could not get product data')
            st.stop()

    if state.time_df.Date.max() != pd.Timestamp(datetime.date.today()):
        update_time_df()

    if 'user' not in state:
        login_page()
    else:
        main_page()


if __name__ == '__main__':
    main()
