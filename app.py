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
st.title("stockscholar.streamlit.app")
st.caption("A beginner-friendly stock dashboard with AI analysis and a AI tutor for investing education.")
with st.expander("Dashboard Settings ⭐", expanded=False):
    st.write("Search for stock tickers:")
    ticker = st.text_input("Enter a stock ticker:", "QBTS")
    #Time period, Chart type, Benchmark selectors
    date_mode = st.selectbox(
        "Choose date mode:",
        ["Preset Period", "Custom Date Range"]
    )
    period = st.selectbox(    
        "Choose a time period:",
        ["1d", "5d", "1mo", "3mo", "6mo", "1y", "5y"],
        index=3
        
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
        [
            "EMA 20","EMA 50","EMA 200","VWAP","Bollinger Bands","RSI","MACD","ATR","Stochastic","OBV","Pivot Points","Volume Bars"
        ],
        default=[
            "EMA 20","EMA 50","VWAP","Volume Bars","RSI"
        ]
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
            interval_options = ["1h", "1d"]
        else:
            interval_options = ["1d", "1wk", "1mo"]

    else:
        if period == "1d":
            interval_options = ["1m", "5m", "15m", "30m", "1h"]
        elif period == "5d":
            interval_options = ["30m", "1h", "1d"]
        elif period == "1mo":
            interval_options = ["1d"]
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

    average_gain = gains.ewm(
        alpha=1 / window,
        adjust=False,
        min_periods=window
    ).mean()
    average_loss = losses.ewm(
        alpha=1 / window,
        adjust=False,
        min_periods=window
    ).mean()

     # Replacing zero with NaN prevents division-by-zero errors.
    rs = average_gain / average_loss.replace(0, float("nan"))
    rsi = 100 - (100 / (1 + rs))
 
     # Handle one-direction and completely flat price windows correctly.
    rsi = rsi.mask((average_loss == 0) & (average_gain > 0), 100)
    rsi = rsi.mask((average_gain == 0) & (average_loss > 0), 0)
    rsi = rsi.mask((average_gain == 0) & (average_loss == 0), 50)
 
    return rsi
def calculate_macd(
    close_prices,
    fast_window=12,
    slow_window=26,
    signal_window=9
):
    fast_ema = close_prices.ewm(
        span=fast_window,
        adjust=False,
        min_periods=fast_window
    ).mean()

    slow_ema = close_prices.ewm(
        span=slow_window,
        adjust=False,
        min_periods=slow_window
    ).mean()

    macd_line = fast_ema - slow_ema

    signal_line = macd_line.ewm(
        span=signal_window,
        adjust=False,
        min_periods=signal_window
    ).mean()

    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def calculate_bollinger_bands(
    close_prices,
    window=20,
    standard_deviations=2
):
    middle_band = close_prices.rolling(
        window=window,
        min_periods=window
    ).mean()

    rolling_std = close_prices.rolling(
        window=window,
        min_periods=window
    ).std(ddof=0)

    upper_band = middle_band + (
        standard_deviations * rolling_std
    )

    lower_band = middle_band - (
        standard_deviations * rolling_std
    )

    return middle_band, upper_band, lower_band


def calculate_atr(data, window=14):
    previous_close = data["Close"].shift(1)

    true_range_parts = pd.concat(
        [
            data["High"] - data["Low"],
            (data["High"] - previous_close).abs(),
            (data["Low"] - previous_close).abs()
        ],
        axis=1
    )

    true_range = true_range_parts.max(axis=1)

    # Wilder-style smoothing for Average True Range
    atr = true_range.ewm(
        alpha=1 / window,
        adjust=False,
        min_periods=window
    ).mean()

    return atr


def calculate_stochastic(
    data,
    window=14,
    smooth_window=3
):
    lowest_low = data["Low"].rolling(
        window=window,
        min_periods=window
    ).min()

    highest_high = data["High"].rolling(
        window=window,
        min_periods=window
    ).max()

    price_range = (
        highest_high - lowest_low
    ).replace(0, float("nan"))

    percent_k = 100 * (
        (data["Close"] - lowest_low) / price_range
    )

    percent_d = percent_k.rolling(
        window=smooth_window,
        min_periods=smooth_window
    ).mean()

    return percent_k, percent_d


def calculate_obv(close_prices, volume):
    price_direction = (
        close_prices.diff().gt(0).astype(int)
        - close_prices.diff().lt(0).astype(int)
    )

    signed_volume = volume * price_direction

    return signed_volume.fillna(0).cumsum()
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
    # Get the latest available price and indicator values.
    current_price = data["Close"].iloc[-1]
    current_volume = data["Volume"].iloc[-1]

    ema_20 = data["EMA_20"].iloc[-1]
    ema_50 = data["EMA_50"].iloc[-1]
    ema_200 = data["EMA_200"].iloc[-1]

    rsi = data["RSI"].iloc[-1]
    vwap = data["VWAP"].iloc[-1]

    macd = data["MACD"].iloc[-1]
    macd_signal = data["MACD_Signal"].iloc[-1]
    macd_histogram = data["MACD_Histogram"].iloc[-1]

    bb_middle = data["BB_Middle"].iloc[-1]
    bb_upper = data["BB_Upper"].iloc[-1]
    bb_lower = data["BB_Lower"].iloc[-1]
    bb_width = data["BB_Width"].iloc[-1]

    atr = data["ATR"].iloc[-1]
    atr_percent = data["ATR_Percent"].iloc[-1]

    stochastic_k = data["Stochastic_K"].iloc[-1]
    stochastic_d = data["Stochastic_D"].iloc[-1]

    current_obv = data["OBV"].iloc[-1]

    analysis = {}

    # --------------------------------------------------
    # EMA TREND
    # --------------------------------------------------

    if pd.notna(ema_20) and pd.notna(ema_50) and pd.notna(ema_200):
        if current_price > ema_20 > ema_50 > ema_200:
            analysis["Trend"] = "Strongly Bullish"
            analysis["Trend Reason"] = (
                "Price is above EMA 20, EMA 50, and EMA 200, "
                "and the shorter averages are above the longer averages."
            )

        elif current_price < ema_20 < ema_50 < ema_200:
            analysis["Trend"] = "Strongly Bearish"
            analysis["Trend Reason"] = (
                "Price is below EMA 20, EMA 50, and EMA 200, "
                "and the shorter averages are below the longer averages."
            )

        elif current_price > ema_20 and ema_20 > ema_50:
            analysis["Trend"] = "Bullish"
            analysis["Trend Reason"] = (
                "Price is above EMA 20, and EMA 20 is above EMA 50, "
                "but the full long-term EMA structure is not bullish."
            )

        elif current_price < ema_20 and ema_20 < ema_50:
            analysis["Trend"] = "Bearish"
            analysis["Trend Reason"] = (
                "Price is below EMA 20, and EMA 20 is below EMA 50, "
                "but the full long-term EMA structure is not bearish."
            )

        elif current_price > ema_50:
            analysis["Trend"] = "Mildly Bullish"
            analysis["Trend Reason"] = (
                "Price is above EMA 50, but the moving averages are mixed."
            )

        elif current_price < ema_50:
            analysis["Trend"] = "Mildly Bearish"
            analysis["Trend Reason"] = (
                "Price is below EMA 50, but the moving averages are mixed."
            )

        else:
            analysis["Trend"] = "Neutral"
            analysis["Trend Reason"] = (
                "Price is close to the main moving averages."
            )

    elif pd.notna(ema_20) and pd.notna(ema_50):
        if current_price > ema_20 > ema_50:
            analysis["Trend"] = "Bullish"
            analysis["Trend Reason"] = (
                "Price is above EMA 20 and EMA 50. EMA 200 is unavailable "
                "because the selected range does not contain enough candles."
            )

        elif current_price < ema_20 < ema_50:
            analysis["Trend"] = "Bearish"
            analysis["Trend Reason"] = (
                "Price is below EMA 20 and EMA 50. EMA 200 is unavailable "
                "because the selected range does not contain enough candles."
            )

        elif current_price > ema_50:
            analysis["Trend"] = "Mildly Bullish"
            analysis["Trend Reason"] = (
                "Price is above EMA 50, but EMA 20 and EMA 50 are not fully aligned."
            )

        else:
            analysis["Trend"] = "Mildly Bearish"
            analysis["Trend Reason"] = (
                "Price is below EMA 50, but EMA 20 and EMA 50 are not fully aligned."
            )

    elif pd.notna(ema_20):
        if current_price > ema_20:
            analysis["Trend"] = "Short-Term Bullish"
            analysis["Trend Reason"] = (
                "Price is above EMA 20. Longer EMAs are unavailable because "
                "the selected range does not contain enough candles."
            )

        elif current_price < ema_20:
            analysis["Trend"] = "Short-Term Bearish"
            analysis["Trend Reason"] = (
                "Price is below EMA 20. Longer EMAs are unavailable because "
                "the selected range does not contain enough candles."
            )

        else:
            analysis["Trend"] = "Short-Term Neutral"
            analysis["Trend Reason"] = "Price is very close to EMA 20."

    else:
        analysis["Trend"] = "Unavailable"
        analysis["Trend Reason"] = (
            "Not enough candles are available to calculate the moving averages."
        )

    # --------------------------------------------------
    # RSI MOMENTUM
    # --------------------------------------------------

    if pd.isna(rsi):
        analysis["Momentum"] = "Unavailable"
        analysis["Momentum Reason"] = (
            "At least 14 candles are needed to calculate RSI."
        )

    elif rsi >= 70:
        analysis["Momentum"] = f"Overbought ({rsi:.1f})"
        analysis["Momentum Reason"] = (
            "RSI is at or above 70, showing strong upward momentum but "
            "also a greater risk that the move is becoming stretched."
        )

    elif rsi >= 55:
        analysis["Momentum"] = f"Bullish ({rsi:.1f})"
        analysis["Momentum Reason"] = (
            "RSI is above 55, showing positive momentum without being overbought."
        )

    elif rsi <= 30:
        analysis["Momentum"] = f"Oversold ({rsi:.1f})"
        analysis["Momentum Reason"] = (
            "RSI is at or below 30, showing strong selling pressure. "
            "Oversold does not guarantee that price will immediately recover."
        )

    elif rsi <= 45:
        analysis["Momentum"] = f"Bearish ({rsi:.1f})"
        analysis["Momentum Reason"] = (
            "RSI is below 45, showing weaker price momentum."
        )

    else:
        analysis["Momentum"] = f"Neutral ({rsi:.1f})"
        analysis["Momentum Reason"] = (
            "RSI is between 45 and 55, which is a neutral momentum range."
        )

    # --------------------------------------------------
    # VWAP
    # --------------------------------------------------

    if pd.isna(vwap):
        analysis["VWAP"] = "Unavailable"
        analysis["VWAP Reason"] = (
            "VWAP could not be calculated because usable volume data is missing."
        )

    else:
        vwap_difference_percent = (
            (current_price - vwap) / vwap
        ) * 100 if vwap != 0 else 0

        if vwap_difference_percent > 0.1:
            analysis["VWAP"] = f"Bullish (${vwap:.2f})"
            analysis["VWAP Reason"] = (
                f"Price is {vwap_difference_percent:.2f}% above VWAP, meaning "
                "it is trading above the volume-weighted average price."
            )

        elif vwap_difference_percent < -0.1:
            analysis["VWAP"] = f"Bearish (${vwap:.2f})"
            analysis["VWAP Reason"] = (
                f"Price is {abs(vwap_difference_percent):.2f}% below VWAP, "
                "meaning it is trading below the volume-weighted average price."
            )

        else:
            analysis["VWAP"] = f"Neutral (${vwap:.2f})"
            analysis["VWAP Reason"] = (
                "Price is within 0.1% of VWAP."
            )

    # --------------------------------------------------
    # PIVOT POINTS
    # --------------------------------------------------

    if (
        pivot_points is not None
        and all(
            pd.notna(pivot_points.get(level))
            for level in ["Pivot", "R1", "S1"]
        )
    ):
        pivot = pivot_points["Pivot"]
        resistance_1 = pivot_points["R1"]
        support_1 = pivot_points["S1"]

        if current_price > resistance_1:
            analysis["Pivot"] = "Bullish Breakout"
            analysis["Pivot Reason"] = (
                f"Price is above R1 resistance at ${resistance_1:.2f}."
            )

        elif current_price > pivot:
            analysis["Pivot"] = "Bullish"
            analysis["Pivot Reason"] = (
                f"Price is above the main pivot level at ${pivot:.2f}."
            )

        elif current_price < support_1:
            analysis["Pivot"] = "Bearish Breakdown"
            analysis["Pivot Reason"] = (
                f"Price is below S1 support at ${support_1:.2f}."
            )

        elif current_price < pivot:
            analysis["Pivot"] = "Bearish"
            analysis["Pivot Reason"] = (
                f"Price is below the main pivot level at ${pivot:.2f}."
            )

        else:
            analysis["Pivot"] = "Neutral"
            analysis["Pivot Reason"] = (
                "Price is very close to the main pivot level."
            )

    else:
        analysis["Pivot"] = "Unavailable"
        analysis["Pivot Reason"] = (
            "Not enough usable data is available to calculate pivot points."
        )

    # --------------------------------------------------
    # VOLUME
    # --------------------------------------------------

    # Exclude the current candle from the average so the current candle
    # is compared with the preceding candles instead of with itself.
    previous_volume = data["Volume"].iloc[:-1].dropna().tail(20)
    average_volume = previous_volume.mean()

    if (
        pd.isna(current_volume)
        or pd.isna(average_volume)
        or average_volume <= 0
    ):
        analysis["Volume"] = "Unavailable"
        analysis["Volume Reason"] = (
            "Not enough usable volume data is available for comparison."
        )

    else:
        volume_ratio = current_volume / average_volume

        if volume_ratio >= 1.5:
            analysis["Volume"] = f"High ({volume_ratio:.2f}x)"
            analysis["Volume Reason"] = (
                "Current volume is at least 1.5 times the average of the "
                "preceding 20 candles."
            )

        elif volume_ratio >= 1:
            analysis["Volume"] = f"Above Average ({volume_ratio:.2f}x)"
            analysis["Volume Reason"] = (
                "Current volume is above the average of the preceding 20 candles."
            )

        else:
            analysis["Volume"] = f"Below Average ({volume_ratio:.2f}x)"
            analysis["Volume Reason"] = (
                "Current volume is below the average of the preceding 20 candles."
            )

    # --------------------------------------------------
    # MACD
    # --------------------------------------------------

    if (
        pd.isna(macd)
        or pd.isna(macd_signal)
        or pd.isna(macd_histogram)
    ):
        analysis["MACD"] = "Unavailable"
        analysis["MACD Reason"] = (
            "At least 34 candles are normally needed before the MACD signal "
            "line becomes available."
        )

    else:
        previous_histogram = None

        if len(data) >= 2:
            possible_previous_histogram = data["MACD_Histogram"].iloc[-2]

            if pd.notna(possible_previous_histogram):
                previous_histogram = possible_previous_histogram

        if macd > macd_signal:
            if (
                previous_histogram is not None
                and macd_histogram > previous_histogram
            ):
                macd_result = "Bullish / Strengthening"

            elif (
                previous_histogram is not None
                and macd_histogram < previous_histogram
            ):
                macd_result = "Bullish / Weakening"

            else:
                macd_result = "Bullish"

            analysis["MACD"] = (
                f"{macd_result} ({macd_histogram:+.3f})"
            )
            analysis["MACD Reason"] = (
                "The MACD line is above the signal line. A rising histogram "
                "suggests bullish momentum is strengthening, while a shrinking "
                "histogram suggests it is weakening."
            )

        elif macd < macd_signal:
            if (
                previous_histogram is not None
                and macd_histogram < previous_histogram
            ):
                macd_result = "Bearish / Strengthening"

            elif (
                previous_histogram is not None
                and macd_histogram > previous_histogram
            ):
                macd_result = "Bearish / Weakening"

            else:
                macd_result = "Bearish"

            analysis["MACD"] = (
                f"{macd_result} ({macd_histogram:+.3f})"
            )
            analysis["MACD Reason"] = (
                "The MACD line is below the signal line. A more negative "
                "histogram suggests bearish momentum is strengthening, while "
                "a histogram moving toward zero suggests it is weakening."
            )

        else:
            analysis["MACD"] = "Neutral"
            analysis["MACD Reason"] = (
                "The MACD and signal lines are currently equal."
            )

    # --------------------------------------------------
    # BOLLINGER BANDS
    # --------------------------------------------------

    bollinger_values = [
        bb_middle,
        bb_upper,
        bb_lower,
        bb_width
    ]

    if any(pd.isna(value) for value in bollinger_values):
        analysis["Bollinger Bands"] = "Unavailable"
        analysis["Bollinger Bands Reason"] = (
            "At least 20 candles are needed to calculate Bollinger Bands."
        )

    else:
        previous_band_widths = (
            data["BB_Width"]
            .iloc[:-1]
            .dropna()
            .tail(20)
        )

        average_band_width = previous_band_widths.mean()

        squeeze_detected = (
            pd.notna(average_band_width)
            and average_band_width > 0
            and bb_width < average_band_width * 0.75
        )

        if current_price > bb_upper:
            bollinger_result = "Above Upper Band"
            bollinger_reason = (
                "Price is above the upper Bollinger Band, showing a strong "
                "but potentially stretched upward move."
            )

        elif current_price < bb_lower:
            bollinger_result = "Below Lower Band"
            bollinger_reason = (
                "Price is below the lower Bollinger Band, showing a strong "
                "but potentially stretched downward move."
            )

        elif current_price >= bb_middle:
            bollinger_result = "Upper Half"
            bollinger_reason = (
                "Price is between the middle and upper Bollinger Bands."
            )

        else:
            bollinger_result = "Lower Half"
            bollinger_reason = (
                "Price is between the middle and lower Bollinger Bands."
            )

        if squeeze_detected:
            bollinger_result += " / Possible Squeeze"
            bollinger_reason += (
                " The bands are unusually narrow compared with their recent "
                "width, suggesting lower volatility and a possible future expansion."
            )

        analysis["Bollinger Bands"] = (
            f"{bollinger_result} ({bb_width:.2f}%)"
        )
        analysis["Bollinger Bands Reason"] = bollinger_reason

    # --------------------------------------------------
    # ATR VOLATILITY
    # --------------------------------------------------

    if pd.isna(atr) or pd.isna(atr_percent):
        analysis["ATR Volatility"] = "Unavailable"
        analysis["ATR Volatility Reason"] = (
            "At least 14 candles are needed to calculate ATR."
        )

    else:
        previous_atr_percentages = (
            data["ATR_Percent"]
            .iloc[:-1]
            .dropna()
            .tail(20)
        )

        average_atr_percent = previous_atr_percentages.mean()

        if (
            pd.isna(average_atr_percent)
            or average_atr_percent <= 0
        ):
            atr_result = "Current Volatility"

        elif atr_percent >= average_atr_percent * 1.25:
            atr_result = "High / Rising"

        elif atr_percent <= average_atr_percent * 0.75:
            atr_result = "Low / Falling"

        else:
            atr_result = "Normal"

        analysis["ATR Volatility"] = (
            f"{atr_result} (${atr:.3f}, {atr_percent:.2f}%)"
        )
        analysis["ATR Volatility Reason"] = (
            "ATR measures the average size of recent price movements. "
            "It measures volatility, not bullish or bearish direction."
        )

    # --------------------------------------------------
    # STOCHASTIC OSCILLATOR
    # --------------------------------------------------

    if pd.isna(stochastic_k) or pd.isna(stochastic_d):
        analysis["Stochastic"] = "Unavailable"
        analysis["Stochastic Reason"] = (
            "At least 16 candles are normally needed for the smoothed "
            "Stochastic Oscillator."
        )

    else:
        previous_k = None
        previous_d = None

        if len(data) >= 2:
            possible_previous_k = data["Stochastic_K"].iloc[-2]
            possible_previous_d = data["Stochastic_D"].iloc[-2]

            if (
                pd.notna(possible_previous_k)
                and pd.notna(possible_previous_d)
            ):
                previous_k = possible_previous_k
                previous_d = possible_previous_d

        bullish_crossover = (
            previous_k is not None
            and previous_d is not None
            and previous_k <= previous_d
            and stochastic_k > stochastic_d
        )

        bearish_crossover = (
            previous_k is not None
            and previous_d is not None
            and previous_k >= previous_d
            and stochastic_k < stochastic_d
        )

        if stochastic_k >= 80 and stochastic_d >= 80:
            if bearish_crossover:
                stochastic_result = "Overbought / Bearish Crossover"
            else:
                stochastic_result = "Overbought"

        elif stochastic_k <= 20 and stochastic_d <= 20:
            if bullish_crossover:
                stochastic_result = "Oversold / Bullish Crossover"
            else:
                stochastic_result = "Oversold"

        elif bullish_crossover:
            stochastic_result = "Bullish Crossover"

        elif bearish_crossover:
            stochastic_result = "Bearish Crossover"

        elif stochastic_k > stochastic_d:
            stochastic_result = "Bullish"

        elif stochastic_k < stochastic_d:
            stochastic_result = "Bearish"

        else:
            stochastic_result = "Neutral"

        analysis["Stochastic"] = (
            f"{stochastic_result} "
            f"(K {stochastic_k:.1f} / D {stochastic_d:.1f})"
        )
        analysis["Stochastic Reason"] = (
            "%K shows where the latest close sits within the recent price "
            "range, while %D is a smoothed version of %K. A crossover is only "
            "reported when the two lines actually switch sides."
        )

    # --------------------------------------------------
    # ON-BALANCE VOLUME
    # --------------------------------------------------

    lookback = min(10, len(data) - 1)

    if lookback < 1 or pd.isna(current_obv):
        analysis["OBV"] = "Unavailable"
        analysis["OBV Reason"] = (
            "Not enough data is available to compare price and OBV direction."
        )

    else:
        earlier_price = data["Close"].iloc[-(lookback + 1)]
        earlier_obv = data["OBV"].iloc[-(lookback + 1)]

        price_change = current_price - earlier_price
        obv_change = current_obv - earlier_obv

        if price_change > 0 and obv_change > 0:
            analysis["OBV"] = "Bullish Confirmation"
            analysis["OBV Reason"] = (
                f"Price and OBV both increased over the last "
                f"{lookback} candles, so volume supports the price increase."
            )

        elif price_change < 0 and obv_change < 0:
            analysis["OBV"] = "Bearish Confirmation"
            analysis["OBV Reason"] = (
                f"Price and OBV both decreased over the last "
                f"{lookback} candles, so volume supports the price decline."
            )

        elif price_change > 0 and obv_change < 0:
            analysis["OBV"] = "Bearish Divergence"
            analysis["OBV Reason"] = (
                f"Price increased while OBV decreased over the last "
                f"{lookback} candles, meaning volume did not confirm the rise."
            )

        elif price_change < 0 and obv_change > 0:
            analysis["OBV"] = "Bullish Divergence"
            analysis["OBV Reason"] = (
                f"Price decreased while OBV increased over the last "
                f"{lookback} candles, meaning volume did not confirm the decline."
            )

        else:
            analysis["OBV"] = "Neutral"
            analysis["OBV Reason"] = (
                f"Price or OBV changed very little over the last "
                f"{lookback} candles."
            )

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
    indicator_names = [
        "Trend",
        "Momentum",
        "VWAP",
        "Pivot",
        "Volume",
        "MACD",
        "Bollinger Bands",
        "ATR Volatility",
        "Stochastic",
        "OBV"
    ]

    # Build one text section containing every indicator result and reason.
    indicator_text = ""

    for indicator_name in indicator_names:
        indicator_value = indicator_analysis.get(
            indicator_name,
            "Unavailable"
        )

        indicator_reason = indicator_analysis.get(
            f"{indicator_name} Reason",
            "No explanation is available."
        )

        indicator_text += f"""
{indicator_name}: {indicator_value}
{indicator_name} reason: {indicator_reason}
"""

    prompt = f"""
Analyze this stock's technical indicators using only the data provided.

Rules:
- Do not give a direct buy, sell, or hold recommendation.
- Do not invent news, earnings, fundamentals, price targets, or missing data.
- Explain both the bullish and bearish evidence.
- Identify signals that conflict with each other.
- Keep the explanation beginner-friendly and reasonably short.
- Treat ATR as a measure of volatility, not bullish or bearish direction.
- Do not count EMA, MACD, RSI, and Stochastic as completely independent evidence because they overlap in measuring trend or momentum.
- Explain whether volume and OBV confirm or weaken the price movement.
- If an indicator says Unavailable, do not guess its value or signal.

Ticker: {ticker.upper()}
Current price: ${current_price:.2f}

Technical indicator results:
{indicator_text}

Format the response exactly like this:

Overall Technical Read:
Bullish Evidence:
Bearish Evidence:
Conflicting Signals:
Volatility and Risk:
Volume Confirmation:
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
    data["EMA_20"] = data["Close"].ewm(
        span=20,
        adjust=False,
        min_periods=20
    ).mean()
    data["EMA_50"] = data["Close"].ewm(
        span=50,
        adjust=False,
        min_periods=50
    ).mean()

    data["EMA_200"] = data["Close"].ewm(
        span=200,
        adjust=False,
        min_periods=200
    ).mean()
    #Calculate VWAP
    data["Typical_Price"] = (
        data["High"] + data["Low"] + data["Close"]
    ) / 3

    cumulative_volume = (
        data["Volume"]
        .fillna(0)
        .cumsum()
    )
    cumulative_price_volume = (
        data["Typical_Price"]
        * data["Volume"].fillna(0)
    ).cumsum()

    data["VWAP"] = (
        cumulative_price_volume
        / cumulative_volume.replace(0, float("nan"))
    )
    #Calculate RSI
    data["RSI"] = calculate_rsi(
        data["Close"]
    )
    #Calculate MACD
    (
        data["MACD"],
        data["MACD_Signal"],
        data["MACD_Histogram"]
    ) = calculate_macd(
        data["Close"]
    )
    #Calculate Bollinger Bands
    (
        data["BB_Middle"],
        data["BB_Upper"],
        data["BB_Lower"]
    ) = calculate_bollinger_bands(
        data["Close"]
    )
    data["BB_Width"] = (
        (
            data["BB_Upper"]
            - data["BB_Lower"]
        )
        / data["BB_Middle"].replace(
            0,
            float("nan")
        )
    ) * 100
    #Calculate ATR
    data["ATR"] = calculate_atr(
        data
    )
    #Express ATR as a percentage of the stock price
    data["ATR_Percent"] = (
        data["ATR"]
        / data["Close"].replace(
            0,
            float("nan")
        )
    ) * 100
    #Calculate Stochastic Oscillator
    (
        data["Stochastic_K"],
        data["Stochastic_D"]
    ) = calculate_stochastic(
        data
    )
    #Calculate On-Balance Volume
    data["OBV"] = calculate_obv(
        data["Close"],
        data["Volume"]
    )
    #Calculate pivot levels
    pivot_points = calculate_pivot_points(data)

    #Analyze all calculated indicators
    indicator_analysis = analyze_indicators(data,pivot_points)

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

    # Stop if stock data has not loaded.
    if (
        "data" not in st.session_state
        or st.session_state.data is None
    ):
        st.error("Data not found.")
        return

    # Stop if indicator analysis has not been created.
    if (
        "indicator_analysis" not in st.session_state
        or st.session_state.indicator_analysis is None
    ):
        st.error("Indicator analysis not found.")
        return

    show_indicator_summary = st.checkbox(
        "Show indicator summary",
        value=False,
        key="show_indicator_summary"
    )

    if not show_indicator_summary:
        st.caption("Indicator summary is hidden.")
        return

    indicator_analysis = st.session_state.indicator_analysis

    # These names must match the keys in analyze_indicators().
    summary_indicators = [
        "Trend",
        "Momentum",
        "VWAP",
        "Pivot",
        "Volume",
        "MACD",
        "Bollinger Bands",
        "ATR Volatility",
        "Stochastic",
        "OBV"
    ]

    # Create three indicator cards per row.
    for row_start in range(0, len(summary_indicators), 3):
        columns = st.columns(3)

        row_indicators = summary_indicators[
            row_start:row_start + 3
        ]

        for column, indicator_name in zip(
            columns,
            row_indicators
        ):
            with column:
                indicator_value = indicator_analysis.get(
                    indicator_name,
                    "Unavailable"
                )

                indicator_reason = indicator_analysis.get(
                    f"{indicator_name} Reason",
                    "No explanation is available."
                )

                st.metric(
                    label=indicator_name,
                    value=indicator_value
                )

                st.caption(indicator_reason)

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
    st.write("Uses same time period as selected above")
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
        "QBTS, SMCI, MU, INTC, IONQ, QUBT,QNT"
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

    comparison_chart_data = comparison_chart_data[:12]
    chart_cols = st.columns(4)

    for index, item in enumerate(comparison_chart_data):
        symbol, compare_data, compare_return, compare_current = item
        chart_column = chart_cols[index % 4]

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
    st.write("Compare a ticker against various benchmarks.")
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
    #Adds Bollinger Bands if selected
    if "Bollinger Bands" in stock_indicators:
        upper_band_trace = go.Scatter(
            x=data.index,
            y=data["BB_Upper"],
            mode="lines",
            name="Bollinger Upper",
            line=dict(dash="dot")
        )

        middle_band_trace = go.Scatter(
            x=data.index,
            y=data["BB_Middle"],
            mode="lines",
            name="Bollinger Middle",
            line=dict(dash="dash")
        )

        lower_band_trace = go.Scatter(
            x=data.index,
            y=data["BB_Lower"],
            mode="lines",
            name="Bollinger Lower",
            line=dict(dash="dot")
        )

        #Add the bands to the price row when volume bars are displayed
        if show_volume:
            chart.add_trace(
                upper_band_trace,
                row=1,
                col=1
            )

            chart.add_trace(
                middle_band_trace,
                row=1,
                col=1
            )

            chart.add_trace(
                lower_band_trace,
                row=1,
                col=1
            )

        #Add the bands to the normal chart when volume is hidden
        else:
            chart.add_trace(
                upper_band_trace
            )

            chart.add_trace(
                middle_band_trace
            )

            chart.add_trace(
                lower_band_trace
            )

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

    #Creates MACD chart if selected
    if "MACD" in stock_indicators:

        #MACD requires enough candles for its signal line.
        if data["MACD_Signal"].dropna().empty:
            st.info(
                "Not enough candles are available to display MACD. "
                "Choose a longer period or a smaller interval."
            )

        else:
            macd_chart = go.Figure()

            #Adds MACD histogram bars
            macd_chart.add_trace(
                go.Bar(
                    x=data.index,
                    y=data["MACD_Histogram"],
                    name="MACD Histogram"
                )
            )

            #Adds MACD line
            macd_chart.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data["MACD"],
                    mode="lines",
                    name="MACD"
                )
            )

            #Adds signal line
            macd_chart.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data["MACD_Signal"],
                    mode="lines",
                    name="Signal Line"
                )
            )

            #Adds the zero reference line
            macd_chart.add_hline(
                y=0,
                line_dash="dot",
                annotation_text="Zero",
                annotation_position="right"
            )

            #Labels the MACD chart
            macd_chart.update_layout(
                title=f"{ticker.upper()} MACD",
                xaxis_title="Date / Time",
                yaxis_title="MACD",
                height=350
            )

            #Removes weekends and closed-market gaps
            macd_chart = remove_chart_gaps(
                macd_chart
            )

            #Displays MACD chart
            st.plotly_chart(
                macd_chart,
                use_container_width=True
            )
    #Creates ATR chart if selected
    if "ATR" in stock_indicators:

        #Check whether ATR contains any usable values
        if data["ATR"].dropna().empty:
            st.info(
                "Not enough candles are available to display ATR. "
                "Choose a longer period or a smaller interval."
            )

        else:
            atr_chart = go.Figure()

            #Adds ATR line
            atr_chart.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data["ATR"],
                    mode="lines",
                    name="ATR"
                )
            )

            #Calculate the recent average ATR
            recent_average_atr = (
                data["ATR"]
                .dropna()
                .tail(20)
                .mean()
            )

            #Add an average ATR reference line
            if pd.notna(recent_average_atr):
                atr_chart.add_hline(
                    y=recent_average_atr,
                    line_dash="dot",
                    annotation_text=(
                        f"Recent Average: "
                        f"${recent_average_atr:.3f}"
                    ),
                    annotation_position="right"
                )

            #Labels the ATR chart
            atr_chart.update_layout(
                title=f"{ticker.upper()} Average True Range",
                xaxis_title="Date / Time",
                yaxis_title="ATR",
                height=300
            )

            #Removes weekends and closed-market gaps
            atr_chart = remove_chart_gaps(
                atr_chart
            )

            #Displays ATR chart
            st.plotly_chart(
                atr_chart,
                use_container_width=True
            )

            #Display the latest ATR values below the chart
            latest_atr = data["ATR"].iloc[-1]
            latest_atr_percent = data["ATR_Percent"].iloc[-1]

            if (
                pd.notna(latest_atr)
                and pd.notna(latest_atr_percent)
            ):
                st.caption(
                    f"Latest ATR: ${latest_atr:.3f} "
                    f"({latest_atr_percent:.2f}% of the share price)"
                )
    #Creates Stochastic Oscillator chart if selected
    if "Stochastic" in stock_indicators:

        #Check whether both Stochastic lines contain usable values
        if (
            data["Stochastic_K"].dropna().empty
            or data["Stochastic_D"].dropna().empty
        ):
            st.info(
                "Not enough candles are available to display the "
                "Stochastic Oscillator. Choose a longer period or "
                "a smaller interval."
            )

        else:
            stochastic_chart = go.Figure()

            #Adds the faster %K line
            stochastic_chart.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data["Stochastic_K"],
                    mode="lines",
                    name="%K"
                )
            )

            #Adds the slower %D signal line
            stochastic_chart.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data["Stochastic_D"],
                    mode="lines",
                    name="%D"
                )
            )

            #Adds overbought reference line
            stochastic_chart.add_hline(
                y=80,
                line_dash="dot",
                annotation_text="Overbought 80",
                annotation_position="right"
            )

            #Adds oversold reference line
            stochastic_chart.add_hline(
                y=20,
                line_dash="dot",
                annotation_text="Oversold 20",
                annotation_position="right"
            )

            #Adds a neutral middle reference line
            stochastic_chart.add_hline(
                y=50,
                line_dash="dot",
                annotation_text="Middle 50",
                annotation_position="right"
            )

            #Labels the Stochastic chart
            stochastic_chart.update_layout(
                title=f"{ticker.upper()} Stochastic Oscillator",
                xaxis_title="Date / Time",
                yaxis_title="Stochastic Value",
                height=325
            )

            #Keep the chart scale between 0 and 100
            stochastic_chart.update_yaxes(
                range=[0, 100]
            )

            #Removes weekends and closed-market gaps
            stochastic_chart = remove_chart_gaps(
                stochastic_chart
            )

            #Displays the Stochastic chart
            st.plotly_chart(
                stochastic_chart,
                use_container_width=True
            )

            #Displays the newest values below the chart
            latest_stochastic_k = data["Stochastic_K"].iloc[-1]
            latest_stochastic_d = data["Stochastic_D"].iloc[-1]

            if (
                pd.notna(latest_stochastic_k)
                and pd.notna(latest_stochastic_d)
            ):
                st.caption(
                    f"Latest values: "
                    f"%K = {latest_stochastic_k:.1f}, "
                    f"%D = {latest_stochastic_d:.1f}"
                )
    #Creates On-Balance Volume chart if selected
    if "OBV" in stock_indicators:

        #Check whether OBV contains usable values
        if data["OBV"].dropna().empty:
            st.info(
                "Usable volume data is not available to display OBV."
            )

        else:
            obv_chart = go.Figure()

            #Adds the OBV line
            obv_chart.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data["OBV"],
                    mode="lines",
                    name="OBV"
                )
            )

            #Calculate a short OBV moving average
            data["OBV_MA_10"] = (
                data["OBV"]
                .rolling(
                    window=10,
                    min_periods=10
                )
                .mean()
            )

            #Only add the moving average when enough candles exist
            if not data["OBV_MA_10"].dropna().empty:
                obv_chart.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data["OBV_MA_10"],
                        mode="lines",
                        name="OBV 10-Candle Average",
                        line=dict(dash="dash")
                    )
                )

            #Labels the OBV chart
            obv_chart.update_layout(
                title=f"{ticker.upper()} On-Balance Volume",
                xaxis_title="Date / Time",
                yaxis_title="Cumulative Volume",
                height=325
            )

            #Format large OBV numbers with commas
            obv_chart.update_yaxes(
                tickformat=","
            )

            #Removes weekends and closed-market gaps
            obv_chart = remove_chart_gaps(
                obv_chart
            )

            #Displays the OBV chart
            st.plotly_chart(
                obv_chart,
                use_container_width=True
            )

            #Display recent OBV direction
            obv_lookback = min(
                10,
                len(data) - 1
            )

            if obv_lookback >= 1:
                latest_obv = data["OBV"].iloc[-1]

                previous_obv = data["OBV"].iloc[
                    -(obv_lookback + 1)
                ]

                obv_change = latest_obv - previous_obv

                if obv_change > 0:
                    obv_direction = "Rising"

                elif obv_change < 0:
                    obv_direction = "Falling"

                else:
                    obv_direction = "Flat"

                st.caption(
                    f"OBV direction over the last "
                    f"{obv_lookback} candles: "
                    f"{obv_direction}"
                )


    #END OF MAIN CHART

# GROQ AI TECHNICAL ANALYSIS
def ai_section():
    st.subheader("AI Analysis:")

    show_ai = st.checkbox(
        "Show AI analysis",
        value=False,
        key="show_ai"
    )

    if not show_ai:
        st.caption("AI analysis is hidden.")
        return
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
    st.subheader("Stock Scholar 🎓")
    st.write("Welcome to the Stock Scholar! I'm an AI assistant here to help you understand investing and stock market concepts.")
    with st.expander("Open Investing Assistant", expanded=False):
        st.write(
        "Ask about investing terms, stock market concepts, financial metrics, or technical indicators."
    )
        if "investing_chat_messages" not in st.session_state:
            st.session_state.investing_chat_messages = []
        suggested_questions = [
            "What does P/E ratio mean?",
            "What is market cap?",
            "What is RSI?",
            "What is the number behind EMA?",
            "What does bullish vs bearish mean?",
            "How do traders use stock indicators?",
            "Explain basic market concepts for new investors.",
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
                    st.session_state.scroll_to_chat = True


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
            st.session_state.scroll_to_chat = True
            st.markdown(
                '<div id="latest-chat-response"></div>',
                unsafe_allow_html=True
            )
            with st.chat_message("assistant"):
                st.write(answer)
        st.divider()
        if st.button("Clear investing assistant chat"):
            st.session_state.investing_chat_messages = []
            st.rerun()

data_section()
chart_section()
st.divider()
st.subheader("Ticker Info/Analysis")
with st.expander(f"{ticker.upper()} Company and Indicator Info Analysis"):
    news_section()
    st.divider()
    indicator_section()
    st.divider()
    ai_section()
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
    "GitHub Repository Link",
    github_url
)
