import streamlit as st
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
from datetime import datetime, timedelta
from plotly.subplots import make_subplots
from groq import Groq


#Ticker Input
st.set_page_config(page_title="Stock Tracker", layout="wide")
st.title("Stock Scholar")
st.caption("A beginner-friendly stock dashboard with AI analysis and investing education.")
with st.expander("Dashboard Settings", expanded=False):
    st.write("Search for stock tickers:")
    ticker = st.text_input("Enter a stock ticker:", "QBTS")
    #Time period, Chart type, Benchmark selectors
    date_mode = st.selectbox(
        "Choose date mode:",
        ["Preset Period", "Custom Date Range"]
    )
    period = st.selectbox(    
        "Choose a time period:",
        ["1d", "5d", "1mo", "3mo", "6mo", "1y", "5y"]
    )
    if date_mode == "Custom Date Range":
        start_date = st.date_input(
            "Start date:",
            datetime.today().date() - timedelta(days=30)
        )

        end_date = st.date_input(
            "End date:",
            datetime.today().date()
        )

        if start_date > end_date:
            st.warning("Start date cannot be after end date.")
    else:
        start_date = None
        end_date = None
    chart_type = st.selectbox(
        "Choose a chart type:",
        ["Candlestick Chart","Line Chart"]
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
    #Changes time between data based on period or custom date range
    if date_mode == "Custom Date Range":
        custom_range_days = (end_date - start_date).days

        if custom_range_days <= 7:
            interval_options = ["1m", "5m", "15m", "30m", "1h"]
        elif custom_range_days <= 30:
            interval_options = ["30m", "1h", "1d"]
        else:
            interval_options = ["1d", "1wk", "1mo"]

    else:
        if period == "1d":
            interval_options = ["1m", "5m", "15m", "30m", "1h"]
        elif period == "5d":
            interval_options = ["15m", "30m", "1h", "1d"]
        elif period == "1mo":
            interval_options = ["30m", "1h", "1d"]
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
        ["1s","5s", "15s", "30s", "60s"],
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
#Sends a prompt to Groq and returns the AI response
def ask_groq(prompt):
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are a stock research assistant. Explain the data clearly. Do not give direct buy or sell recommendations. Ensure that your response uses consistent font and format big numbers so that they are easy to read."
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
def remove_chart_gaps(fig):
    chart_rangebreaks = [
        dict(bounds=["sat", "mon"])
    ]

    if not extended_hours and interval in ["1m", "5m", "10m", "15m", "30m", "1h"]:
        chart_rangebreaks.append(
            dict(bounds=[16, 9.5], pattern="hour")
        )

    fig.update_xaxes(rangebreaks=chart_rangebreaks)

    return fig
#Downloads stock history using either preset period or custom date range
def get_stock_history(stock_object):
    if date_mode == "Custom Date Range":
        if start_date > end_date:
            return pd.DataFrame()

        return stock_object.history(
            start=start_date,
            end=end_date + timedelta(days=1),
            interval=interval,
            prepost=extended_hours
        )

    return stock_object.history(
        period=period,
        interval=interval,
        prepost=extended_hours
    )
#AI tutor for explaining investing and market concepts
def ask_investing_tutor(user_question):
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": """
You are an investing education assistant inside a beginner-friendly stock dashboard.

Your job:
- Explain investing, stock market, company, and technical-analysis concepts clearly.
- Use beginner-friendly language.
- Give examples when helpful.
- Explain terms like P/E, EPS, market cap, RSI, VWAP, EMA, volume, revenue, profit, debt, cash flow, and benchmarks.
- Do not give direct buy, sell, or hold recommendations.
- Do not tell the user what stock to buy.
- If the user asks for advice, explain what factors they should research instead.
- Keep responses clear and not too long.
"""
                },
                {
                    "role": "user",
                    "content": user_question
                }
            ],
            temperature=0.3
        )

        return response.choices[0].message.content

    except Exception as error:
        return f"AI tutor error: {error}"

#Downloads stock data and calculates shared values for the dashboard
@st.fragment(run_every=run_rate)
def data_section():
    data = get_stock_history(stock)

    if data.empty:
        st.session_state.data = None
        return

    #Calculate indicators
    data["EMA_20"] = data["Close"].ewm(span=20, adjust=False).mean()
    data["EMA_50"] = data["Close"].ewm(span=50, adjust=False).mean()
    data["EMA_200"] = data["Close"].ewm(span=200, adjust=False).mean()

    data["Typical_Price"] = (data["High"] + data["Low"] + data["Close"]) / 3
    data["VWAP"] = (data["Typical_Price"] * data["Volume"]).cumsum() / data["Volume"].cumsum()

    data["RSI"] = calculate_rsi(data["Close"])
    pivot_points = calculate_pivot_points(data)
    indicator_analysis = analyze_indicators(data, pivot_points)

    #Calculate price values
    starting_price = data["Close"].iloc[0]
    current_price = data["Close"].iloc[-1]
    percent_change = ((current_price - starting_price) / starting_price) * 100

    #Calculate price range values
    pd_low = data["Low"].min()
    pd_high = data["High"].max()

    if pd_high != pd_low:
        range_position = (current_price - pd_low) / (pd_high - pd_low)
    elif current_price == pd_high:
        range_position = 1
    else:
        range_position = 0.5

    range_position = max(0, min(range_position, 1))

    #Save shared values so other sections can use them
    st.session_state.data = data
    st.session_state.pivot_points = pivot_points
    st.session_state.indicator_analysis = indicator_analysis
    st.session_state.current_price = current_price
    st.session_state.percent_change = percent_change
    st.session_state.pd_low = pd_low
    st.session_state.pd_high = pd_high
    st.session_state.range_position = range_position
@st.fragment(run_every=run_rate)
def news_section():
    st.subheader(f"Recent News for {ticker.upper()}")

    show_news = st.checkbox(
        "Show news",
        value=False,
        key="show_news"
    )

    if not show_news:
        st.caption("News is hidden.")
        return

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
@st.fragment(run_every=run_rate)
def indicator_section():

    st.subheader("Indicator Summary")    
    if "data" not in st.session_state or st.session_state.data is None:
        st.error("Data not found.")
        return

    indicator_analysis = st.session_state.indicator_analysis
    show_indicator_summary = st.checkbox(
        "Show indicator summary",
        value=False,
        key="show_indicator_summary"
    )

    if not show_indicator_summary:
        st.caption("Indicator summary is hidden.")
        return


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

@st.fragment(run_every=run_rate)
def company_section():
    st.subheader("Company Profile")

    show_company_profile = st.checkbox(
        "Show company profile",
        value=False,
        key="show_company_profile"
    )

    if not show_company_profile:
        st.caption("Company profile is hidden.")
        return

    display_company_profile(stock, ticker)

@st.fragment(run_every=run_rate)
def comparison_section():
    st.subheader("Ticker Comparison")

    show_comparison = st.checkbox(
        "Show ticker comparison",
        value=False,
        key="show_comparison"
    )

    if not show_comparison:
        st.caption("Ticker comparison is hidden.")
        return

    comp_table_input = st.text_input(
        "Enter tickers to compare, separated by commas:",
        "QBTS, SMCI, MU, INTC"
    )

    st.subheader("Ticker Comparison Table")

    compare_tickers = [
        symbol.strip().upper()
        for symbol in comp_table_input.split(",")
        if symbol.strip() != ""
    ]

    comparison_chart_data = []
    comparison_rows = []

    for symbol in compare_tickers:
        compare_stock = yf.Ticker(symbol)

        compare_data = get_stock_history(compare_stock)

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

    comparison_chart_data = comparison_chart_data[:6]
    chart_cols = st.columns(3)

    for index, item in enumerate(comparison_chart_data):
        symbol, compare_data, compare_return, compare_current = item
        chart_column = chart_cols[index % 3]

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
            mini_chart = remove_chart_gaps(mini_chart)
            st.plotly_chart(mini_chart, use_container_width=True)

@st.fragment(run_every=run_rate)
def benchmark_section():
    st.subheader("Benchmark Comparison")
    if "data" not in st.session_state or st.session_state.data is None:
        st.error("Data not found.")
        return


    show_benchmark = st.checkbox(
        "Show benchmark comparison chart",
        value=False
    )
    
    data = st.session_state.data
    percent_change = st.session_state.percent_change

    if show_benchmark:

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

        benchmark_stock = yf.Ticker(benchmark_symbols[benchmark])

        benchmark_data = get_stock_history(benchmark_stock)

        if benchmark_data.empty:
            st.warning("Benchmark data not found.")
            return

        stock_percent = ((data["Close"] - data["Close"].iloc[0]) / data["Close"].iloc[0]) * 100
        benchmark_percent = ((benchmark_data["Close"] - benchmark_data["Close"].iloc[0]) / benchmark_data["Close"].iloc[0]) * 100

        benchmark_return = benchmark_percent.iloc[-1]

        c1, c2 = st.columns(2)

        with c1:
            st.metric(
                label=f"{benchmark} Return",
                value=f"{benchmark_return:.2f}%"
            )

        with c2:
            st.metric(
                label=f"{ticker.upper()} Return",
                value=f"{percent_change:.2f}%"
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
        comparison_chart = remove_chart_gaps(comparison_chart)
        st.plotly_chart(comparison_chart, use_container_width=True)

@st.fragment(run_every=run_rate)
def chart_section():
    #Stops the section if data has not loaded yet
    if "data" not in st.session_state or st.session_state.data is None:
        st.error("Data not found.")
        return

    #Reads shared values created by data_section()
    data = st.session_state.data
    pivot_points = st.session_state.pivot_points
    indicator_analysis = st.session_state.indicator_analysis
    current_price = st.session_state.current_price
    percent_change = st.session_state.percent_change
    pd_low = st.session_state.pd_low
    pd_high = st.session_state.pd_high
    range_position = st.session_state.range_position

#Displays ticker name, price and percent change
    st.metric(
    label=f"{ticker.upper()} Current Share Price",
    value=f"${current_price:.3f}",
    delta=f"{percent_change:.2f}%",
    )
    if date_mode == "Custom Date Range":
        st.write(f"Price Range from {start_date} to {end_date}")
    else:
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
    chart = remove_chart_gaps(chart)
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
        rsi_chart = remove_chart_gaps(rsi_chart)
        st.plotly_chart(rsi_chart, use_container_width=True)

    #END OF MAIN CHART
# GROQ AI TECHNICAL ANALYSIS
def ai_section():
    st.subheader("AI Analysis:")
    if "data" not in st.session_state or st.session_state.data is None:
        st.warning("Stock data is not ready yet.")
        return
    # Create saved storage spots for both AI responses
    if "indicator_ai_response" not in st.session_state:
        st.session_state.indicator_ai_response = None

    if "company_ai_response" not in st.session_state:
        st.session_state.company_ai_response = None


    if st.button("Generate AI Stock Indicator Analysis"):
        prompt = create_indicator_prompt(
            ticker=ticker,
            current_price=st.session_state.current_price,
            indicator_analysis=st.session_state.indicator_analysis
        )

        with st.spinner("Generating Groq AI indicator analysis..."):
            st.session_state.indicator_ai_response = ask_groq(prompt)

    if st.session_state.indicator_ai_response is not None:
        st.write("AI Stock Indicator Analysis")
        st.write(st.session_state.indicator_ai_response)


    if st.button("Generate AI Company Data Analysis"):
        prompt = create_info_prompt(
            ticker=ticker,
            company_info=stock.info
        )

        with st.spinner("Generating Groq AI company analysis..."):
            st.session_state.company_ai_response = ask_groq(prompt)

    if st.session_state.company_ai_response is not None:
        st.write("AI Company Data Analysis")
        st.write(st.session_state.company_ai_response)

#Chatbot that explains investing and stock market concepts
def investing_chatbot_section():
    st.subheader("Investing Learning Assistant")

    st.write(
        "Ask about investing terms, stock market concepts, financial metrics, or technical indicators."
    )

    if "investing_chat_messages" not in st.session_state:
        st.session_state.investing_chat_messages = []
    suggested_questions = [
        "What does P/E ratio mean?",
        "What is market cap?",
        "What is RSI?",
        "What is VWAP?",
        "What does bullish vs bearish mean?",
        "How do I compare a stock to a benchmark?"
    ]

    st.write("Try asking:")

    suggestion_cols = st.columns(2)

    for index, question in enumerate(suggested_questions):
        with suggestion_cols[index % 2]:
            if st.button(question, key=f"suggestion_{index}"):
                st.session_state.investing_chat_messages.append(
                    {"role": "user", "content": question}
                )

                answer = ask_investing_tutor(question)

                st.session_state.investing_chat_messages.append(
                    {"role": "assistant", "content": answer}
                )



    for message in st.session_state.investing_chat_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    user_question = st.chat_input("Ask an investing question...")

    if user_question:
        st.session_state.investing_chat_messages.append(
            {"role": "user", "content": user_question}
        )

        with st.chat_message("user"):
            st.write(user_question)

        with st.spinner("Explaining concept..."):
            answer = ask_investing_tutor(user_question)

        st.session_state.investing_chat_messages.append(
            {"role": "assistant", "content": answer}
        )

        with st.chat_message("assistant"):
            st.write(answer)

    if st.button("Clear investing assistant chat"):
        st.session_state.investing_chat_messages = []
        st.rerun()
#Run section functions
#Run section functions
data_section()
chart_section()
st.divider()
news_section()
st.divider()
ai_section()
st.divider()
indicator_section()
st.divider()
company_section()
st.divider()
comparison_section()
st.divider()
benchmark_section()
st.divider()
investing_chatbot_section()
st.divider()
github_url = "https://github.com/baballama/stock-project"
st.link_button(
    "GitHub Repository",
    github_url
)