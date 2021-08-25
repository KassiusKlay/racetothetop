mkdir -p ~/app/.streamlit
echo "[server]
headless = true
port = $PORT
enableCORS = false
" > ~/.streamlit/config.toml

echo $dropbox > ~/app/.streamlit/secrets.toml
