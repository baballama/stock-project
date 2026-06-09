import streamlit as st
import yfinance as yf
import plotly.express as px

st.title("Stock Tracker")

st.write("Search for stock tickers:")

ticker = st.text_input("Enter a stock ticker:", "INTC")

pd = st.selectbox(
    "Choose a time period:",
    ["1d","5d", "1mo", "3mo", "6mo", "1y", "5y"]
)

stock = yf.Ticker(ticker)

data = stock.history(period=pd)

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