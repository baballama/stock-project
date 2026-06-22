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

    Week 6/14-6/20    
    *6/15-6/16
    -added a period price range bar, git commit
    -added a new feature where you can insert multiple tickers and compare their data within a table 
    -6/17
    -added smaller charts alongside the table to allow visual comparison
        max of 6 charts to prevent slowness
    -6/18
        Lighter day
            figured out how to retrieve recent news articles for tickers using yfinance news
    -6/20-6/21
        Added a recent news section using yfinance news
            -shows most 5 most recent news articles with their titles and summaries
            -displays publication dates
            -the news feature will be improving later on
        Changed web layout to "wide"
            made more use of space, allowing me to increase columns of the comparison charts from 2 to 3



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
    
    
    






Next Features:
AI analysis of stock indicators 
News section, possibly AI analysis
Portfolio tracker


