import streamlit as st
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go

#Ticker Input
st.title("Stock Tracker")
st.write("Search for stock tickers:")
ticker = st.text_input("Enter a stock ticker:", "SMCI")
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


    

    # st.subheader(f"Recent {ticker.upper()} ticker data")
    # st.write(data.tail(5)) Change to company data
    # st.caption(f"{interval} intervals")
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
#Displays percentage change for both stock and benchmark
        st.metric(
        label=f"{benchmark} Return",
        value=f"{benchmark_return:.2f}%"
        )
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
#Run chart_section function
chart_section()