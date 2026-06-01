import streamlit as st
import yfinance as yf

st.title("Stock Tracker")

st.write("Search for a stock ticker")

ticker = st.text_input("Enter a stock ticker:", "INTC")

stock = yf.Ticker(ticker)

data = stock.history(period="1mo")

st.subheader(f"{ticker} ticker data")

st.write(data.tail())