Progress Log

Week 1 5/24-5/30
    *5/29-5/30
    created project folder, 
        -set up progress log & README
        -created github repository, installed git
        -imported pandas, yfinance, streamlit, plotly for later in the project
        -set up venv
    , learned what each of these do
Added stock indicator 

Week 2 5/31-6/6
    *5/31
    -connected local project folder to github repo
    -made 1st git commit
    *6/1
    -used yfinance to pull real stock data, 
    -streamlit to launch the web app, 
    -added basic functions: input box for tickers that retrieves stock data using yfinance and displays the most recent rows of data
    -fixed up the README and progress log
    -used plotly to create closing price chart
    -added timeframe input
    -deployed app using streamlit
`   *6/2-6/8
    -break from the project focusing on drivers ed course


Week 3 6/7-6/13
    *6/9
    -changed the time period selector to a drop down menu to support later changes
        -git commit
    -researched how i could potentially incorporate an AI analyst into the app using recent news and data pulled from yfinance or somewhere else
    -learned about candlestick patterns (started adding them to the app using plotly) 
        -also learned candlestick patterns and identified them using historical stock data
    *6/10
    -Implemented a candlestick chart option into the project
    -Added a checkbox to include/exclude pre/post market data
    -added a time interval dropdown that allow you to pick the intervals between prices
        options change based on time period selected
    -git commit
    -added a auto data refresh for the chart (not fully live) along with current ticker price with refresh speed selection
    *6/11
    -Percentage indicator up/down from market open added
    -git commit
    -started working on the next feature (Benchmark comparison: chart, percentage change, dropdown selector)
    *6/12
    -continued working on benchmark comparison chart
    *6/13
    -finished working on benchmark comparison chart
        -separate line graph with both the selected ticker and benchmark compared using a percentage based graph with both starting at 0% from the beginning of the selected time period
        -exact percentage change also displayed
        -color coded


    Week 4 6/14-6/20    
    *6/15-6/16
    -added a period price range bar, git commit
    -added a new feature where you can insert multiple tickers and compare their data within a table 
    -6/17
    -added smaller charts alongside the table to allow visual comparison
        max of 6 charts to prevent slowness
    -6/18
        Lighter day
            figured out how to retrieve recent news articles for tickers using yfinance news


    Week 5 6/21-27
    -6/20-6/21
        Added a recent news section using yfinance news
            -shows most 5 most recent news articles with their titles and summaries
            -displays publication dates
            -the news feature will be improving later on
        Changed web layout to "wide"
            made more use of space, allowing me to increase columns of the comparison charts from 2 to 3
            -git commit
    -6/21-6/24
        Researched stock indicators including EMA, VWAP, Pivot points, RSI, MACD, Bollinger Bands and how to read them
            -shifted main focus of project to a more functional stock tracker and researcher
        Added some stock indicators to the project
            -select which indicators you want to show on the chart
            -current options: "EMA 20", "EMA 50", "EMA 200", "VWAP", "RSI", "Pivot Points", "Volume Bars",
    -6/26
        Researched how to analyze indicators together
            -learned EMA = trend, VWAP = buyer/seller control, RSI = momentum, Pivot Points = support/resistance, Volume = confirmation
        Planned next feature: AI analysis of all indicators together
            -decided to use calculated indicator values first, then have AI explain the bullish/bearish case
            -looked into Ollama for local AI explanations
    -6/27-6/28
        Added indicator reader feature
            -uses calculated EMA, VWAP, RSI, Pivot Points, and Volume values to create a simple technical summary
            -shows trend, momentum, VWAP position, pivot position, and volume confirmation
        Added local Ollama AI analysis
            -uses the indicator reader results to generate a bullish and bearish explanation
            -keeps the AI analysis based on data to prevent hallucinations




Current Features
    -Basic stock tracking features
        -Ticker input, Time period selector, Time between prices selector

    -Line Chart and Candlestick chart dropdown menu

    -Auto Update feature
        -Dropdown with options for refresh rate

    -Option to include/exclude pre/post market data

    -Benchmark comparison
        -Dropdown for selecting U.S benchmarks (S&P 500, Nasdaq, Dow Jones, Russell 2000)
        -Separate color coded line graph comparing the selected ticker and benchmark using a percentage change system

    -Price range bar
        -displays high, low, current price on a line
        -currently a bit ugly (will improve it later on)

    -Multiple ticker comparison
        -Input tickers separated by commas which are then displayed in a table with the latest price, period return, period low and high
        -Mini charts under the table that display price over time of selected tickers from the table

    -Recent News
        -shows most 5 most recent news articles with their titles and summaries
        -displays publication dates
        -the news feature will be improving later on

    -Stock indicators
        -select which indicators you want to show on the chart
        -current options: "EMA 20", "EMA 50", "EMA 200", "VWAP", "RSI", "Pivot Points", "Volume Bars",

    Indicator explanation feature
        -uses calculated EMA, VWAP, RSI, Pivot Points, and Volume values to create a simple technical summary
        -shows trend, momentum, VWAP position, pivot position, and volume confirmation

    -Local Ollama AI analysis
        -uses Ollama to analyze the stock indicators locally and summarize them 






Next Features:
AI analysis on the actual web app not just local
AI analysis of recent news
Portfolio tracker
Table of contents in code to make reading it easier

