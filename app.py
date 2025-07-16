import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from nsetools import Nse
from streamlit_autorefresh import st_autorefresh

nse = Nse()

# Auto refresh every 30 seconds
st_autorefresh(interval=30 * 1000, key="auto_refresh")

st.set_page_config(page_title="NSE vs BSE Comparator", layout="wide")
st.title("📊 NSE vs BSE Stock Price Comparator (Real-Time)")

# Load stock mapping
df_stocks = pd.read_csv("stocks.csv")

# Cache to reduce redundant calls during development
@st.cache_data(ttl=30)
def get_nse_price(symbol):
    try:
        quote = nse.get_quote(symbol)
        if isinstance(quote, dict) and 'lastPrice' in quote:
            return float(quote['lastPrice'].replace(',', ''))
        return None
    except:
        return None

def get_bse_price(bse_code):
    try:
        url = f"https://www.bseindia.com/stock-share-price/stockreach_stockdetails.aspx?scripcode={bse_code}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        price_tag = soup.find('span', id='ContentPlaceHolder1_lblLastTradedPrice')
        if price_tag:
            return float(price_tag.text.replace(',', '').strip())
    except:
        return None

def calculate_difference(nse_price, bse_price):
    if nse_price and bse_price:
        return round(((nse_price - bse_price) / ((nse_price + bse_price) / 2)) * 100, 2)
    return None

data = []

with st.spinner("Fetching live data..."):
    for _, row in df_stocks.iterrows():
        name = row['name']
        nse_symbol = row['nse_symbol']
        bse_code = str(row['bse_code'])

        nse_price = get_nse_price(nse_symbol)
        bse_price = get_bse_price(bse_code)
        diff = calculate_difference(nse_price, bse_price)

        data.append({
            "Stock": name,
            "NSE Price (₹)": nse_price,
            "BSE Price (₹)": bse_price,
            "Difference (%)": diff
        })

df_result = pd.DataFrame(data)
st.dataframe(df_result.style.format({
    "NSE Price (₹)": "₹{:.2f}",
    "BSE Price (₹)": "₹{:.2f}",
    "Difference (%)": "{:.2f}%"
}), height=600)

st.caption("🔁 Auto-refreshes every 30 seconds. Built with free data scraping, may not be 100% accurate.")