import streamlit as st
import pandas as pd
import db
from init import init_page
from user import user_page
from streamlit import session_state as state
import concurrent.futures
# from user import get_product_data
import numpy as np
from currency_converter import CurrencyConverter
import datetime
from cryptocmd import CmcScraper
import yfinance as yf

APP = 'portfolio'
CREDS = 'user_credentials.xlsx'
DF = 'df.xlsx'


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


def update_time_df():
    c = CurrencyConverter()
    fx_rate = c.convert(1, 'USD')

    df = pd.merge(state.df, state.products_df)
    c = CurrencyConverter()
    fx_rate = c.convert(1, 'USD')
    df['Value'] = df.Amount * df.Price * fx_rate

    df = df.groupby('User').agg({'Value': 'sum'}).reset_index()
    df['Date'] = datetime.date.today()
    df = pd.concat([state.time_df, df])

    dbx = db.get_dropbox_client()
    db.upload_dataframe(dbx, APP, df, 'time_df.xlsx')


def main():
    dbx = db.get_dropbox_client()
    if 'user_credentials' not in state:
        try:
            state.user_credentials = db.download_dataframe(dbx, APP, CREDS)
            state.df = db.download_dataframe(dbx, APP, DF)
            state.time_df = db.download_dataframe(dbx, APP, 'time_df.xlsx')
            state.products_df = get_all_products_daily_price_and_pct_change()
        except Exception as e:
            st.error('Could not download files from database.')
            st.write(e)
            st.stop()

    if state.time_df.Date.max() != datetime.date.today():
        update_time_df()

    if 'user' not in state:
        init_page()
    else:
        user_page()


if __name__ == '__main__':
    main()
