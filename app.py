import streamlit as st
import yfinance as yf
import plotly.express as px

st.title("Stock Tracker")

st.write("Search for stock tickers:")

ticker = st.text_input("Enter a stock ticker:", "INTC")

period = st.text_input("Enter a time frame (e.g. 1y, 1mo, 1d):", "1y")

stock = yf.Ticker(ticker)

data = stock.history(period=period)

st.subheader(f"{ticker.upper()} ticker data")

st.write(data.tail(10))

st.subheader(f"{ticker.upper()} Closing Price Chart")

chart = px.line(
    data,
    x=data.index,
    y="Close",
    title=f"{ticker.upper()} Closing Price Over time"
)

st.plotly_chart(chart)