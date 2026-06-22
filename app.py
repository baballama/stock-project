import streamlit as st
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

#Ticker Input
st.set_page_config(page_title="Stock Tracker", layout="wide")
st.title("Stock Tracker")
st.write("Search for stock tickers:")
ticker = st.text_input("Enter a stock ticker:", "QBTS")
#Time period, Chart type, Benchmark selectors
period = st.selectbox(
    "Choose a time period:",
    ["1d", "5d", "1mo", "3mo", "6mo", "1y", "5y"]
)
chart_type = st.selectbox(
    "Choose a chart type:",
    ["Candlestick Chart","Line Chart"]
)
benchmark = st.selectbox(
    "Choose a benchmark to compare against:",
    ["S&P 500", "Nasdaq Composite", "Dow Jones", "Russell 2000"]
)

#Benchmark name-> Ticker (dict)
benchmark_symbols = {
    "S&P 500": "^GSPC",
    "Nasdaq Composite": "^IXIC",
    "Dow Jones": "^DJI",
    "Russell 2000": "^RUT"
}
#Show benchmark t/f
show_benchmark = st.checkbox(
    "Show benchmark comparison chart",
    value=False
)


#Turns ticker into yfinance object
stock = yf.Ticker(ticker)
#Changes time between data based on period
if period == "1d":
    interval_options = ["1m", "5m", "15m", "30m", "1h"]
elif period == "5d":
    interval_options = ["1h", "1d"]
else:
    interval_options = ["1d", "1wk", "1mo"]

#Select time intervals, pre/post market data, auto-refresh and refresh rate
interval = st.selectbox(
    "Choose a time interval:",
    interval_options
)
extended_hours = st.checkbox(
    "Include pre/post-market data",
    value=False
)
auto_refresh = st.checkbox(
    "Auto-refresh data",
    value=False
)
refresh_speed = st.selectbox(
    "Refresh speed:",
    ["5s", "15s", "30s", "60s"],
    index=2
)
#If auto-refresh is checked run chart_section at the refresh speed
if auto_refresh:
    run_rate = refresh_speed
else:
    run_rate = None
@st.fragment(run_every=run_rate)
def chart_section():
#Downloads variable stock's history using customization from above
    data = stock.history(
        period=period,
        interval=interval,
        prepost=extended_hours
    )
#Prevent crashes if yfinance doesnt return anything
    if data.empty:
        st.error("Data not found.")
        return

#News section
    st.subheader(f"Recent News for {ticker.upper()}")

    try:
        news_items = stock.news

        if not news_items:
            st.write("No recent news found.")
        else:
            for i, item in enumerate(news_items[:5], start=1):
                content = item.get("content", {})
                title = content.get("title", "No title available")
                news_summary = content.get("summary", "No summary available")
                publish_date = content.get("pubDate", "Date not available")
                st.subheader(f"{i}.) {title}")
                st.caption(f"Published: {publish_date}")
                st.write(news_summary)

    except Exception as error:
        st.warning("News data could not be loaded.")
        st.caption(f"Error: {error}")





#Uses stock history data to retrieve starting and current price and uses that to calculate percent change
    starting_price = data["Close"].iloc[0]
    current_price = data["Close"].iloc[-1]
    percent_change = ((current_price - starting_price) / starting_price) * 100
#Displays ticker name, price and percent change
    st.metric(
    label=f"{ticker.upper()} Current Share Price",
    value=f"${current_price:.3f}",
    delta=f"{percent_change:.2f}%",
    )
# Calculate the lowest and highest prices during the selected period
    pd_low = data["Low"].min()
    pd_high = data["High"].max()
# Calculate where the current price sits between the period low and high
    if pd_high != pd_low:
        range_position = (current_price - pd_low) / (pd_high - pd_low)
    elif current_price ==pd_high:
        range_position = 1
    else:
        range_position = 0.5
# Keep the position between 0 and 1 so the progress bar does not break
    range_position = max(0, min(range_position, 1))

    st.write(f"Price Range throughout {period}")

    st.progress(range_position)

    col_low, col_current, col_high = st.columns(3)

    with col_low:
        st.caption(f"Low: ${pd_low:.2f}")

    with col_current:
        st.caption(f"Current: ${current_price:.2f}")

    with col_high:
        st.caption(f"High: ${pd_high:.2f}")
#MAIN CHART FOR THE SELECTED TICKER

#Line chart selected->create line chart from data variable store it in chart var, else create candlestick chart in chart variable
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
#Labels graph
        chart.update_layout(
            title=f"{ticker.upper()} Candlestick Chart",
            xaxis_title="Date / Time",
            yaxis_title="Price"
        )

    st.plotly_chart(chart, use_container_width=True)
#END OF MAIN CHART




#MULTIPLE TICKER COMPARISON
#Ticker comparison table input
    comp_table_input = st.text_input(
        "Enter tickers to compare, separated by commas:",
        "QBTS, SMCI, SPCX"
    )
    st.subheader("Ticker Comparison Table")
#Turns input into a list
    compare_tickers = [
        symbol.strip().upper()
        for symbol in comp_table_input.split(",")
        if symbol.strip() != ""
    ]
    comparison_chart_data = []
    comparison_rows = []

    for symbol in compare_tickers:
        compare_stock = yf.Ticker(symbol)

        compare_data = compare_stock.history(
            period=period,
            interval=interval,
            prepost=extended_hours
        )

        if compare_data.empty:
            comparison_rows.append({
                "Ticker": symbol,
                "Latest Price": "Data not found",
                "Period Return": "N/A",
                "Period Low": "N/A",
                "Period High": "N/A"
            })
            continue

        compare_start = compare_data["Close"].iloc[0]
        compare_current = compare_data["Close"].iloc[-1]
        compare_return = ((compare_current - compare_start) / compare_start) * 100
        compare_low = compare_data["Low"].min()
        compare_high = compare_data["High"].max()

        comparison_rows.append({
            "Ticker": symbol,
            "Latest Price": f"${compare_current:.2f}",
            "Period Return": f"{compare_return:.2f}%",
            "Period Low": f"${compare_low:.2f}",
            "Period High": f"${compare_high:.2f}"
        })
        comparison_chart_data.append(
            (symbol, compare_data, compare_return, compare_current)
        )

    st.table(comparison_rows)
# Limit the number of charts to 6
    comparison_chart_data = comparison_chart_data[:6]

# Create 3 columns so charts appear side by side
    chart_cols = st.columns(3)

    for index, item in enumerate(comparison_chart_data):
    #Unpacks ticker chart info from tuple into separate variables    
        symbol, compare_data, compare_return, compare_current = item
 # Choose which column the chart should go into
        chart_column = chart_cols[index % 3]
#
        with chart_column:
            st.write(f"{symbol}")
            st.metric(
                label="Latest Price",
                value=f"${compare_current:.2f}",
                delta=f"{compare_return:.2f}%"
            )
            mini_chart = px.line(
                compare_data,
                x=compare_data.index,
                y="Close",
                title=f"{symbol} Price Chart"
            )
            mini_chart.update_layout(
                height=250,
                margin=dict(l=10, r=10, t=40, b=10),
                showlegend=False,
                xaxis_title="",
                yaxis_title=""
            )
            st.plotly_chart(mini_chart, use_container_width=True)
#END OF MULTIPLE TICKER COMPARISON


#BENCHMARK     
#If benchmark option selected create yfinance object from selected benchmark and gather its data, check for empty data    
    if show_benchmark:
        benchmark_stock = yf.Ticker(benchmark_symbols[benchmark])
        benchmark_data = benchmark_stock.history(
            period=period,
            interval=interval,
            prepost=extended_hours
        )
        if benchmark_data.empty:
            st.warning("Benchmark data not found.")
            return
#Converts the share price into a percentage change startting from 0% so that both benchmark and stock can be graphed on the same chart
        stock_percent = ((data["Close"] - data["Close"].iloc[0]) / data["Close"].iloc[0]) * 100    
        benchmark_percent = ((benchmark_data["Close"] - benchmark_data["Close"].iloc[0]) / benchmark_data["Close"].iloc[0]) * 100
#Overall percent change for benchmark stock from start to end of selected period
        benchmark_return = benchmark_percent.iloc[-1]
#Displays percentage change for both stock and benchmark (side by side))
        c1,c2=st.columns(2)
        with c1:
            st.metric(
            label=f"{benchmark} Return",
            value=f"{benchmark_return:.2f}%"
            )
        with c2:
            st.metric(
            label=f"{ticker.upper()} Return",
            value=f"{percent_change:.2f}%",
            )
        st.subheader(f"{ticker.upper()} vs {benchmark}")
#Create plotly figure
        comparison_chart = go.Figure()
#Adds separate line for both stock and benchmark
        comparison_chart.add_trace(
            go.Scatter(
                x=data.index,
                y=stock_percent,
                mode="lines",
                name=ticker.upper()
            )
        )
        comparison_chart.add_trace(
            go.Scatter(
                x=benchmark_data.index,
                y=benchmark_percent,
                mode="lines",
                name=benchmark
            )
        )
#Labels graph
        comparison_chart.update_layout(
            title=f"Percent Return Comparison: {ticker.upper()} vs {benchmark}",
            xaxis_title="Date / Time",
            yaxis_title="Percent Return"
        )

        st.plotly_chart(comparison_chart, use_container_width=True)    
#END OF BENCHMARK SECTION

#Run chart_section function
chart_section()