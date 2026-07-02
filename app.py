import streamlit as st
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
from datetime import datetime
from plotly.subplots import make_subplots
from groq import Groq


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
#Stock indicator dropdown selector
stock_indicators = st.multiselect(
    "Choose stock indicators to display:",
    ["EMA 20", "EMA 50", "EMA 200", "VWAP", "RSI", "Pivot Points", "Volume Bars"],
    default=["EMA 20", "EMA 50", "VWAP", "Volume Bars"]
)
st.caption("Indicators are calculated using the selected chart interval.")
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

#Calculate indicators functions
def calculate_rsi(close_prices, window=14):
    price_change = close_prices.diff()

    gains = price_change.clip(lower=0)
    losses = -price_change.clip(upper=0)

    average_gain = gains.rolling(window=window).mean()
    average_loss = losses.rolling(window=window).mean()

    rs = average_gain / average_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_pivot_points(data):
    if len(data) < 2:
        return None

    previous_high = data["High"].iloc[-2]
    previous_low = data["Low"].iloc[-2]
    previous_close = data["Close"].iloc[-2]

    pivot = (previous_high + previous_low + previous_close) / 3

    resistance_1 = (2 * pivot) - previous_low
    support_1 = (2 * pivot) - previous_high

    resistance_2 = pivot + (previous_high - previous_low)
    support_2 = pivot - (previous_high - previous_low)

    return {
        "Pivot": pivot,
        "R1": resistance_1,
        "S1": support_1,
        "R2": resistance_2,
        "S2": support_2
    }
    #Analyzes all indicators together using simple rules
def analyze_indicators(data, pivot_points):
    current_price = data["Close"].iloc[-1]
    current_volume = data["Volume"].iloc[-1]

    ema_20 = data["EMA_20"].iloc[-1]
    ema_50 = data["EMA_50"].iloc[-1]
    ema_200 = data["EMA_200"].iloc[-1]
    rsi = data["RSI"].iloc[-1]
    vwap = data["VWAP"].iloc[-1]

    average_volume = data["Volume"].tail(20).mean()

    analysis = {}

    #Analyze EMA trend
    if current_price > ema_20 > ema_50 > ema_200:
        analysis["Trend"] = "Bullish"
        analysis["Trend Reason"] = "Price is above EMA 20, EMA 50, and EMA 200."
    elif current_price < ema_20 < ema_50 < ema_200:
        analysis["Trend"] = "Bearish"
        analysis["Trend Reason"] = "Price is below EMA 20, EMA 50, and EMA 200."
    elif current_price > ema_50:
        analysis["Trend"] = "Mildly Bullish"
        analysis["Trend Reason"] = "Price is above EMA 50, but the full EMA structure is not strongly bullish."
    elif current_price < ema_50:
        analysis["Trend"] = "Mildly Bearish"
        analysis["Trend Reason"] = "Price is below EMA 50, showing weaker medium-term trend."
    else:
        analysis["Trend"] = "Neutral"
        analysis["Trend Reason"] = "Price is close to the main moving averages."

    #Analyze RSI momentum
    if rsi >= 70:
        analysis["Momentum"] = "Strong / Overbought"
        analysis["Momentum Reason"] = "RSI is above 70, showing strong momentum but higher pullback risk."
    elif rsi >= 50:
        analysis["Momentum"] = "Bullish"
        analysis["Momentum Reason"] = "RSI is above 50, showing positive momentum."
    elif rsi <= 30:
        analysis["Momentum"] = "Weak / Oversold"
        analysis["Momentum Reason"] = "RSI is below 30, showing heavy selling pressure but possible bounce risk."
    else:
        analysis["Momentum"] = "Bearish"
        analysis["Momentum Reason"] = "RSI is below 50, showing weaker momentum."

    #Analyze VWAP
    if current_price > vwap:
        analysis["VWAP"] = "Bullish"
        analysis["VWAP Reason"] = "Price is above VWAP, meaning buyers are trading above the volume-weighted average price."
    elif current_price < vwap:
        analysis["VWAP"] = "Bearish"
        analysis["VWAP Reason"] = "Price is below VWAP, meaning sellers are trading below the volume-weighted average price."
    else:
        analysis["VWAP"] = "Neutral"
        analysis["VWAP Reason"] = "Price is very close to VWAP."

    #Analyze pivot points
    if pivot_points is not None:
        pivot = pivot_points["Pivot"]
        r1 = pivot_points["R1"]
        s1 = pivot_points["S1"]

        if current_price > r1:
            analysis["Pivot"] = "Bullish Breakout"
            analysis["Pivot Reason"] = "Price is above R1 resistance."
        elif current_price > pivot:
            analysis["Pivot"] = "Bullish"
            analysis["Pivot Reason"] = "Price is above the main pivot level."
        elif current_price < s1:
            analysis["Pivot"] = "Bearish Breakdown"
            analysis["Pivot Reason"] = "Price is below S1 support."
        elif current_price < pivot:
            analysis["Pivot"] = "Bearish"
            analysis["Pivot Reason"] = "Price is below the main pivot level."
        else:
            analysis["Pivot"] = "Neutral"
            analysis["Pivot Reason"] = "Price is close to the main pivot level."
    else:
        analysis["Pivot"] = "Unavailable"
        analysis["Pivot Reason"] = "Not enough data to calculate pivot points."

    #Analyze volume
    if current_volume > average_volume * 1.5:
        analysis["Volume"] = "High"
        analysis["Volume Reason"] = "Current volume is much higher than the recent 20-candle average."
    elif current_volume > average_volume:
        analysis["Volume"] = "Above Average"
        analysis["Volume Reason"] = "Current volume is above the recent 20-candle average."
    else:
        analysis["Volume"] = "Normal / Weak"
        analysis["Volume Reason"] = "Current volume is not strongly above the recent average."

    return analysis

# #Sends indicator data to Ollama for AI explanation
# def generate_ollama_analysis(ticker, current_price, indicator_analysis, model_name="llama3.1"):
#     prompt = f"""
# You are helping analyze a stock dashboard.

# Use ONLY the indicator information below.
# Do not invent company news, earnings, price targets, or fundamentals.
# Do not give direct buy/sell financial advice.

# Ticker: {ticker}
# Current price: ${current_price:.2f}

# Trend: {indicator_analysis["Trend"]}
# Trend reason: {indicator_analysis["Trend Reason"]}

# Momentum: {indicator_analysis["Momentum"]}
# Momentum reason: {indicator_analysis["Momentum Reason"]}

# VWAP: {indicator_analysis["VWAP"]}
# VWAP reason: {indicator_analysis["VWAP Reason"]}

# Pivot: {indicator_analysis["Pivot"]}
# Pivot reason: {indicator_analysis["Pivot Reason"]}

# Volume: {indicator_analysis["Volume"]}
# Volume reason: {indicator_analysis["Volume Reason"]}

# Write the analysis in this format:

# Overall Technical Read:
# Bullish Case:
# Bearish Case:
# What To Watch:
# Beginner Explanation:

# Keep it clear, balanced, and not too long.
# """

#     response = requests.post(
#         "http://localhost:11434/api/generate",
#         json={
#             "model": model_name,
#             "prompt": prompt,
#             "stream": False
#         }
#     )

#     if response.status_code != 200:
#         return "AI analysis could not be generated. Make sure Ollama is running."

#     return response.json()["response"]


#GROQ PROMPT FUNCTION
#Sends a prompt to Groq and returns the AI response
def ask_groq(prompt):
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are a stock research assistant. Explain the data clearly. Do not give direct buy or sell recommendations. Ensure that your response uses consistent font."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3
        )

        return response.choices[0].message.content

    except Exception as error:
        return f"AI analysis error: {error}"
#Creates a prompt using the calculated indicator summary
def create_indicator_prompt(ticker, current_price, indicator_analysis):
    prompt = f"""
Analyze this stock's technical indicators using only the data provided.

Do not give a direct buy or sell recommendation.
Do not invent news, earnings, fundamentals, or price targets.
Explain both the bullish and bearish case.
Keep the explanation beginner-friendly and not too long.

Ticker: {ticker.upper()}
Current price: ${current_price:.2f}

Trend: {indicator_analysis["Trend"]}
Trend reason: {indicator_analysis["Trend Reason"]}

Momentum: {indicator_analysis["Momentum"]}
Momentum reason: {indicator_analysis["Momentum Reason"]}

VWAP: {indicator_analysis["VWAP"]}
VWAP reason: {indicator_analysis["VWAP Reason"]}

Pivot: {indicator_analysis["Pivot"]}
Pivot reason: {indicator_analysis["Pivot Reason"]}

Volume: {indicator_analysis["Volume"]}
Volume reason: {indicator_analysis["Volume Reason"]}

Format the answer like this:

Overall Technical Read:
Bullish Case:
Bearish Case:
What To Watch:
Beginner Explanation:
"""
    return prompt    

#Formats large numbers like market cap into readable text
def format_large_number(number):
    if number is None:
        return "N/A"

    try:
        number = float(number)

        if number >= 1_000_000_000_000:
            return f"${number / 1_000_000_000_000:.2f}T"
        elif number >= 1_000_000_000:
            return f"${number / 1_000_000_000:.2f}B"
        elif number >= 1_000_000:
            return f"${number / 1_000_000:.2f}M"
        else:
            return f"${number:,.2f}"

    except:
        return "N/A"

#Formats percentages like dividend yield into readable text
def format_percent(number):
    if number is None:
        return "N/A"

    try:
        return f"{number * 100:.2f}%"

    except:
        return "N/A"

#Suggests a benchmark based on the company's sector
def suggest_benchmark(sector):
    if sector is None:
        return "S&P 500"

    sector = sector.lower()

    if "technology" in sector:
        return "Nasdaq Composite"
    elif "communication" in sector:
        return "Nasdaq Composite"
    elif "financial" in sector:
        return "S&P 500"
    elif "healthcare" in sector:
        return "S&P 500"
    elif "energy" in sector:
        return "S&P 500"
    elif "industrial" in sector:
        return "S&P 500"
    elif "consumer cyclical" in sector:
        return "S&P 500"
    elif "consumer defensive" in sector:
        return "S&P 500"
    elif "real estate" in sector:
        return "S&P 500"
    elif "utilities" in sector:
        return "S&P 500"
    else:
        return "S&P 500"

#Displays company profile and fundamental data from yfinance
def display_company_profile(stock, ticker):
    try:
        company_info = stock.info

        company_name = company_info.get("longName", ticker.upper())
        sector = company_info.get("sector", "N/A")
        industry = company_info.get("industry", "N/A")
        website = company_info.get("website", "N/A")
        country = company_info.get("country", "N/A")
        exchange = company_info.get("exchange", "N/A")
        quote_type = company_info.get("quoteType", "N/A")
        business_summary = company_info.get("longBusinessSummary", "No business summary available.")

        market_cap = company_info.get("marketCap")
        trailing_pe = company_info.get("trailingPE")
        forward_pe = company_info.get("forwardPE")
        eps = company_info.get("trailingEps")
        dividend_yield = company_info.get("dividendYield")
        beta = company_info.get("beta")
        fifty_two_week_high = company_info.get("fiftyTwoWeekHigh")
        fifty_two_week_low = company_info.get("fiftyTwoWeekLow")

        suggested_benchmark = suggest_benchmark(sector)

        st.subheader("Company Profile")

        st.write(f"### {company_name}")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Ticker", ticker.upper())
            st.metric("Sector", sector)
            st.metric("Industry", industry)

        with col2:
            st.metric("Market Cap", format_large_number(market_cap))
            st.metric("P/E Ratio", "N/A" if trailing_pe is None else f"{trailing_pe:.2f}")
            st.metric("Forward P/E", "N/A" if forward_pe is None else f"{forward_pe:.2f}")

        with col3:
            st.metric("EPS", "N/A" if eps is None else f"${eps:.2f}")
            st.metric("Dividend Yield", format_percent(dividend_yield))
            st.metric("Beta", "N/A" if beta is None else f"{beta:.2f}")

        col4, col5, col6 = st.columns(3)

        with col4:
            st.metric("52 Week High", "N/A" if fifty_two_week_high is None else f"${fifty_two_week_high:.2f}")

        with col5:
            st.metric("52 Week Low", "N/A" if fifty_two_week_low is None else f"${fifty_two_week_low:.2f}")

        with col6:
            st.metric("Suggested Benchmark", suggested_benchmark)

        st.write(f"**Exchange:** {exchange}")
        st.write(f"**Quote Type:** {quote_type}")
        st.write(f"**Country:** {country}")
        st.write(f"**Website:** {website}")

        with st.expander("Business Summary"):
            st.write(business_summary)

        with st.expander("Raw Company Data"):
            st.json(company_info)

    except Exception as error:
        st.warning("Company profile could not be loaded.")
        st.caption(f"Error: {error}")


#Creates a prompt using the calculated indicator summary
#Creates a prompt for AI company profile analysis
def create_info_prompt(ticker, company_info):
    company_name = company_info.get("longName", ticker.upper())
    sector = company_info.get("sector", "N/A")
    industry = company_info.get("industry", "N/A")
    website = company_info.get("website", "N/A")
    country = company_info.get("country", "N/A")
    exchange = company_info.get("exchange", "N/A")
    quote_type = company_info.get("quoteType", "N/A")
    business_summary = company_info.get("longBusinessSummary", "No business summary available.")

    market_cap = company_info.get("marketCap", "N/A")
    trailing_pe = company_info.get("trailingPE", "N/A")
    forward_pe = company_info.get("forwardPE", "N/A")
    eps = company_info.get("trailingEps", "N/A")
    dividend_yield = company_info.get("dividendYield", "N/A")
    beta = company_info.get("beta", "N/A")

    fifty_two_week_high = company_info.get("fiftyTwoWeekHigh", "N/A")
    fifty_two_week_low = company_info.get("fiftyTwoWeekLow", "N/A")
    current_price = company_info.get("currentPrice", "N/A")

    total_revenue = company_info.get("totalRevenue", "N/A")
    revenue_growth = company_info.get("revenueGrowth", "N/A")
    gross_margins = company_info.get("grossMargins", "N/A")
    profit_margins = company_info.get("profitMargins", "N/A")
    operating_margins = company_info.get("operatingMargins", "N/A")

    total_cash = company_info.get("totalCash", "N/A")
    total_debt = company_info.get("totalDebt", "N/A")
    free_cashflow = company_info.get("freeCashflow", "N/A")
    operating_cashflow = company_info.get("operatingCashflow", "N/A")

    analyst_rating = company_info.get("recommendationKey", "N/A")
    target_mean_price = company_info.get("targetMeanPrice", "N/A")
    number_of_analyst_opinions = company_info.get("numberOfAnalystOpinions", "N/A")

    prompt = f"""
Analyze this company's profile and fundamentals using only the data provided.

Do not give a direct buy or sell recommendation.
Do not invent missing data.
Do not make up news, earnings results, or future price targets.
If a value says N/A, explain that the data is unavailable.
Keep the explanation beginner-friendly.

Ticker: {ticker.upper()}
Company name: {company_name}
Sector: {sector}
Industry: {industry}
Country: {country}
Exchange: {exchange}
Quote type: {quote_type}
Website: {website}

Business summary:
{business_summary}

Valuation:
Market cap: {market_cap}
Current price: {current_price}
Trailing P/E: {trailing_pe}
Forward P/E: {forward_pe}
EPS: {eps}
Dividend yield: {dividend_yield}
Beta: {beta}

52-week range:
52-week high: {fifty_two_week_high}
52-week low: {fifty_two_week_low}

Revenue and margins:
Total revenue: {total_revenue}
Revenue growth: {revenue_growth}
Gross margins: {gross_margins}
Profit margins: {profit_margins}
Operating margins: {operating_margins}

Cash flow and balance sheet:
Total cash: {total_cash}
Total debt: {total_debt}
Free cash flow: {free_cashflow}
Operating cash flow: {operating_cashflow}

Analyst data:
Analyst rating: {analyst_rating}
Mean target price: {target_mean_price}
Number of analyst opinions: {number_of_analyst_opinions}

Format the answer like this:

Company Overview:
What The Company Does:
Industry / Sector Context:
Valuation Check:
Financial Strength:
Growth / Profitability:
Risk Factors:
Good Benchmark To Compare Against:
Beginner Explanation:
"""
    return prompt




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
#Calculates EMA, RSI and Pivot Points and stores them in the data variable
    data["EMA_20"] = data["Close"].ewm(span=20, adjust=False).mean()
    data["EMA_50"] = data["Close"].ewm(span=50, adjust=False).mean()
    data["EMA_200"] = data["Close"].ewm(span=200, adjust=False).mean()
    data["Typical_Price"] = (data["High"] + data["Low"] + data["Close"]) / 3
    data["VWAP"] = (data["Typical_Price"] * data["Volume"]).cumsum() / data["Volume"].cumsum()

    data["RSI"] = calculate_rsi(data["Close"])
    pivot_points = calculate_pivot_points(data)

    indicator_analysis = analyze_indicators(data, pivot_points)

#News section
    st.subheader(f"Recent News for {ticker.upper()}")
#check if news data available, if not display message, if error occurs display error message, else display news items (up to 5)
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
#If error occurs while loading news data, display warning and error message
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

    #Checks if volume bars are selected
    show_volume = "Volume Bars" in stock_indicators

    #Creates 2-row chart if volume is selected
    if show_volume:
        chart = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.75, 0.25]
        )
    #Creates normal chart if volume is not selected
    else:
        chart = go.Figure()

    #Creates line chart if selected
    if chart_type == "Line Chart":
        price_trace = go.Scatter(
            x=data.index,
            y=data["Close"],
            mode="lines",
            name="Close"
        )

    #Creates candlestick chart if selected
    else:
        price_trace = go.Candlestick(
            x=data.index,
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"],
            name="Candlestick"
        )

    #Adds price chart to correct chart row
    if show_volume:
        chart.add_trace(price_trace, row=1, col=1)
    else:
        chart.add_trace(price_trace)

    #Matches indicator names to data columns
    ema_choices = {
        "EMA 20": "EMA_20",
        "EMA 50": "EMA_50",
        "EMA 200": "EMA_200"
    }

    #Adds selected EMA lines
    for indicator_name, column_name in ema_choices.items():
        if indicator_name in stock_indicators:
            ema_trace = go.Scatter(
                x=data.index,
                y=data[column_name],
                mode="lines",
                name=indicator_name
            )

            #Adds EMA to price row if volume chart exists
            if show_volume:
                chart.add_trace(ema_trace, row=1, col=1)
            else:
                chart.add_trace(ema_trace)

        #Adds VWAP line if selected
    if "VWAP" in stock_indicators:
        vwap_trace = go.Scatter(
            x=data.index,
            y=data["VWAP"],
            mode="lines",
            name="VWAP"
        )

        #Adds VWAP to price row if volume chart exists
        if show_volume:
            chart.add_trace(vwap_trace, row=1, col=1)
        else:
            chart.add_trace(vwap_trace)

    #Adds pivot point lines if selected
    if "Pivot Points" in stock_indicators and pivot_points is not None:

        #Sets pivot color based on theme
        if st.get_option("theme.base") == "dark":
            pivot_color = "white"
        else:
            pivot_color = "black"

        #Adds each pivot level as a horizontal line
        for level_name, level_price in pivot_points.items():
            if show_volume:
                chart.add_hline(
                    y=level_price,
                    line_dash="dot",
                    line_color=pivot_color,
                    annotation_text=level_name,
                    annotation_position="right",
                    annotation_font_color=pivot_color,
                    row=1,
                    col=1
                )
            else:
                chart.add_hline(
                    y=level_price,
                    line_dash="dot",
                    line_color=pivot_color,
                    annotation_text=level_name,
                    annotation_position="right",
                    annotation_font_color=pivot_color
                )

    #Adds volume bars if selected
    if show_volume:
        chart.add_trace(
            go.Bar(
                x=data.index,
                y=data["Volume"],
                name="Volume"
            ),
            row=2,
            col=1
        )

        #Labels price and volume axes
        chart.update_yaxes(title_text="Price", row=1, col=1)
        chart.update_yaxes(title_text="Volume", row=2, col=1)

    #Labels main chart
    chart.update_layout(
        title=f"{ticker.upper()} Stock Chart",
        xaxis_title="Date / Time",
        yaxis_title="Price",
        height=700
    )

    #Displays main chart
    st.plotly_chart(chart, use_container_width=True)

    #Creates RSI chart if selected
    if "RSI" in stock_indicators:
        rsi_chart = go.Figure()

        #Adds RSI line
        rsi_chart.add_trace(
            go.Scatter(
                x=data.index,
                y=data["RSI"],
                mode="lines",
                name="RSI"
            )
        )

        #Adds overbought reference line
        rsi_chart.add_hline(
            y=70,
            line_dash="dot",
            annotation_text="Overbought 70",
            annotation_position="right"
        )

        #Adds oversold reference line
        rsi_chart.add_hline(
            y=30,
            line_dash="dot",
            annotation_text="Oversold 30",
            annotation_position="right"
        )

        #Labels RSI chart
        rsi_chart.update_layout(
            title=f"{ticker.upper()} RSI",
            xaxis_title="Date / Time",
            yaxis_title="RSI",
            height=300
        )

        #Displays RSI chart
        st.plotly_chart(rsi_chart, use_container_width=True)

    #END OF MAIN CHART
#GROQ AI TECHNICAL ANALYSIS
    st.subheader("AI Technical Analysis")

    if st.button("Generate Groq AI Stock Indicator Analysis"):
        prompt = create_indicator_prompt(
            ticker=ticker,
            current_price=current_price,
            indicator_analysis=indicator_analysis
        )

        with st.spinner("Generating Groq AI analysis..."):
            ai_response = ask_groq(prompt)

        st.write(ai_response)
#Automatic TECHNICAL INDICATOR SUMMARY
    st.subheader("Technical Indicator Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Trend", indicator_analysis["Trend"])
        st.caption(indicator_analysis["Trend Reason"])

    with col2:
        st.metric("Momentum", indicator_analysis["Momentum"])
        st.caption(indicator_analysis["Momentum Reason"])

    with col3:
        st.metric("VWAP", indicator_analysis["VWAP"])
        st.caption(indicator_analysis["VWAP Reason"])

    col4, col5 = st.columns(2)

    with col4:
        st.metric("Pivot", indicator_analysis["Pivot"])
        st.caption(indicator_analysis["Pivot Reason"])

    with col5:
        st.metric("Volume", indicator_analysis["Volume"])
        st.caption(indicator_analysis["Volume Reason"])

    #     #OLLAMA AI TECHNICAL ANALYSIS
    # st.subheader("AI Technical Analysis")

    # if st.button("Generate AI Technical Analysis"):
    #     with st.spinner("Generating AI analysis..."):
    #         ai_analysis = generate_ollama_analysis(
    #             ticker=ticker.upper(),
    #             current_price=current_price,
    #             indicator_analysis=indicator_analysis
    #         )

    #     st.write(ai_analysis)
#run/stop company data function
    company_data_display = st.selectbox(
        "Display/Hide Company data:",
        ["Display Company Data","Hide Company Data"]
    )

    if company_data_display == "Display Company Data":
        display_company_profile(stock, ticker)
    else:
        st.write("Company data is hidden. Select 'Display Company Data' to view it.")

    st.subheader("AI Company Data Analysis")

    if st.button("Generate Groq AI Analysis"):
        prompt = create_info_prompt(
            ticker=ticker,
            company_info=stock.info
        )

        with st.spinner("Generating Groq AI analysis..."):
            ai_response = ask_groq(prompt)

        st.write(ai_response)
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
