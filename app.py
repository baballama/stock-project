import streamlit as st
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go

st.title("Stock Tracker")

st.write("Search for stock tickers:")

ticker = st.text_input("Enter a stock ticker:", "SMCI")

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

benchmark_symbols = {
    "S&P 500": "^GSPC",
    "Nasdaq Composite": "^IXIC",
    "Dow Jones": "^DJI",
    "Russell 2000": "^RUT"
}

show_benchmark = st.checkbox(
    "Show benchmark comparison chart",
    value=False
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

auto_refresh = st.checkbox(
    "Auto-refresh data",
    value=False
)


refresh_speed = st.selectbox(
    "Refresh speed:",
    ["5s", "15s", "30s", "60s"],
    index=2
)
    
if auto_refresh:
    run_rate = refresh_speed
else:
    run_rate = None

@st.fragment(run_every=run_rate)
def chart_section():

    data = stock.history(
        period=period,
        interval=interval,
        prepost=extended_hours
    )

    if data.empty:
        st.error("Data not found, check for spelling errors.")
        return


    

    # st.subheader(f"Recent {ticker.upper()} ticker data")
    # st.write(data.tail(5)) Change to company data
    # st.caption(f"{interval} intervals")

    starting_price = data["Close"].iloc[0]
    current_price = data["Close"].iloc[-1]

    percent_change = ((current_price - starting_price) / starting_price) * 100
    
    st.metric(
    label=f"{ticker.upper()} Current Share Price",
    value=f"${current_price:.3f}",
    delta=f"{percent_change:.2f}%",
    )

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

        stock_percent = ((data["Close"] - data["Close"].iloc[0]) / data["Close"].iloc[0]) * 100    

        benchmark_percent = ((benchmark_data["Close"] - benchmark_data["Close"].iloc[0]) / benchmark_data["Close"].iloc[0]) * 100

        benchmark_return = benchmark_percent.iloc[-1]

        st.metric(
        label=f"{benchmark} Return",
        value=f"{benchmark_return:.2f}%"
        )
        st.metric(
        label=f"{ticker.upper()} Return",
        value=f"{percent_change:.2f}%",
        )
        st.subheader(f"{ticker.upper()} vs {benchmark}")

        comparison_chart = go.Figure()

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

        comparison_chart.update_layout(
            title=f"Percent Return Comparison: {ticker.upper()} vs {benchmark}",
            xaxis_title="Date / Time",
            yaxis_title="Percent Return"
        )

        st.plotly_chart(comparison_chart, use_container_width=True)    

chart_section()