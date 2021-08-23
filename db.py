import dropbox
import pandas as pd
import streamlit as st
from io import StringIO
from pathlib import Path


def upload_file(dbx, app, file):
    with open(file, 'rb') as f:
        dbx.files_upload(
                f.read(),
                f'/{app}/{file}',
                mode=dropbox.files.WriteMode.overwrite)


def dowload_file(dbx, app, file):
    _, f = dbx.files_download(f'/{app}/{file}')
    f = f.content
    s = str(f, 'latin9')
    data = StringIO(s)
    return data


def download_dataframe(dbx, app, file):
    _, f = dbx.files_download(f'/{app}/{file}')
    f = f.content
    df = pd.read_excel(f)
    return df


def upload_dataframe(dbx, app, df, file):
    df.to_excel(file, index=False)
    upload_file(dbx, app, file)
    Path.unlink(Path(file))


def get_dropbox_client():
    dbx = dropbox.Dropbox(st.secrets['dropbox'])
    return dbx
