import streamlit as st
import yfinance as yf
import pandas as pd
import db
from init import init
from user import user
from cryptocmd import CmcScraper
from streamlit import session_state as state

APP = 'portfolio'
CREDS = 'user_credentials.xlsx'


def main():
    dbx = db.get_dropbox_client()
    if 'user_credentials' not in state:
        try:
            state.user_credentials = db.download_dataframe(dbx, APP, CREDS)
        except Exception:
            st.error('Could not download files from database.')
            st.stop()

    if 'user' not in state:
        init()
    else:
        user()


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
