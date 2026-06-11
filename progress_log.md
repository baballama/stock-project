Progress Log

Week 5/24-5/30
    *5/29-5/30
    created project folder, 
        -set up progress log & README
        -created github repository, installed git
        -imported pandas, yfinance, streamlit, plotly for later in the project
        -set up venv
    , learned what each of these do
Week 5/31-6/6
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
Week 6/7-6/13
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
    -added a auto data refresh for the chart (not fully live) along with current ticker price


Current Features
    Basic stock tracking features (Ticker input, Time period selector)
    Line Chart and Candlestick chart dropdown menu
    Auto Update feature with options for refresh rate
    Option to include/exclude pre/post market data
    
