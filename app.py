import streamlit as st
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go

st.title("Stock Tracker")

st.write("Search for stock tickers:")

ticker = st.text_input("Enter a stock ticker:", "QBTS")

period = st.selectbox(
    "Choose a time period:",
    ["1d", "5d", "1mo", "3mo", "6mo", "1y", "5y"]
)

chart_type = st.selectbox(
    "Choose a chart type:",
    ["Candlestick Chart","Line Chart"]
)

stock = yf.Ticker(ticker)

if period == "1d":
    interval_options = ["1m", "5m", "15m", "30m", "1h"]
elif period == "5d":
    interval_options = ["1h", "1d"]
else:
    interval_options = ["1d", "1wk", "1mo"]

interval = st.selectbox(
    "Choose a time interval:",
    interval_options
)

extended_hours = st.checkbox(
    "Include pre/post-market data",
    value=False
)

data = stock.history(
    period=period,
    interval=interval,
    prepost=extended_hours
)

st.subheader(f"Recent {ticker.upper()} ticker data")

##st.write(data.tail(5)) Change to company data

st.caption(f"{interval} intervals")

st.subheader(f"{ticker.upper()} Price Chart")

if chart_type == "Line Chart":
    chart = px.line(
        data,
        x=data.index,
        y="Close",
        title=f"{ticker.upper()} Share Price Over Time"
    )

else:
    chart = go.Figure(
        data=[
            go.Candlestick(
                x=data.index,
                open=data["Open"],
                high=data["High"],
                low=data["Low"],
                close=data["Close"]
            )
        ]
    )

    chart.update_layout(
        title=f"{ticker.upper()} Candlestick Chart",
        xaxis_title="Date / Time",
        yaxis_title="Price"
    )

st.plotly_chart(chart, use_container_width=True)
