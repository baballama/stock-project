Progress Log (CHECK CURRENT FEATURES MORE DETAILED DESCRIPTIONS)

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

    Week 6 6/28-7/4
    -6/29
        Researched alternatives to Ollama for AI analysis that could work on the website
            Landed on Groq
        Created an API key to connect it to my web app
            Kept the key hidden using .gitignore and a separate file
        git commit
    -7/1   
        Replaced the old Ollama indicator analysis with Groq so that it works on the web app, not just locally
            -Same prompt as the Ollama analysis
        Added a disclosure surrounding AI usage in the readme
            -git commit
        Added more to the list of next features
    -7/2
        Added Company data section and AI analysis check "Current Features" for more details
        git commit
    -7/3
        Added a separate Ai section at the bottom of the web app
            -Moved AI analysis buttons into this section
            -Prevents auto-refresh from erasing the summaries

    Week 7 7/5-/7/11
    -7/5
        Fixed an issue where generating one AI analysis would remove the other
        Updated progress log
            -Added more next features 
        git commit
    -7/6
        Shifted focus of the project to be a beginner friendly stock tracker that helps you learn concepts such as stock indicators
            -Will add beginner friendly explanations throughout the website
        Reorganized all of the code into separate sections instead of one big refreshing chart_section
            -Allows me to organize layout easier in the future by letting me make different sections auto-refresh or not
        git commit
    -7/7
        -updated README
        -started working on removing gaps in the charts to make the charts look more professional
    -7/10
        -removed gaps for weekends and pre/postmarket (when its disabled) in all charts
    -7/11
        -added alternative option to select specific start/end date for data retrieval
            Makes it so users can customize what time period they see in order to allow them to track price movement from specific dates such as earnings

    Week 8
    -7/12&7/13
        -added an AI chatbot assistant that helps users learn investing terms and concepts
            -has suggested questions so users have a better idea of what to ask
            -
        -made many sections have show/hide button to make the website less crowded
            news sections, comparison section, company profile section 
        -added dividers between different sections to make it less overwhelming and more organized
        -moved benchmark options into its section
        git commit
    Changed name from Market Mentor to Stock Scholar
        new link, stockscholar.streamlit.app
        removed old website link file
        added github repo link to website
    -7/15 & 7/16
        -added option to show/hide ai analysis
        -fixed an issue where opening the website automatically scrolls to the investing tutor chatbot
        -organized the web app by compressing different sections together with expanders
        -added some design to the web app using emojis to make it less confusing
    -7/17-7/19
        -added 5 new stock indicators, Bollinger Bands, MACD, ATR, Stochastic, OBV
            updated the stock indicator AI analysis and the indicator summary
        
    Week 9 7/19-7/25
       7/23
        -added a dropdown selector for ticker comparison section with options between percentage comparison chart and separate price charts
        -used percentage return code from the benchmark comparison section
        -git commit

        -used AI to generate a beginner guide to stockscholar using expanders

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
        -Alternative option to have one chart with multiple tickers percentage return displayed based on the selected period 


    -Recent News
        -shows most 5 most recent news articles with their titles and summaries
        -displays publication dates
        -the news feature will be improving later on

    -Stock indicators
        -select which indicators you want to show on the chart
        -current options: "EMA 20", "EMA 50", "EMA 200", "VWAP", "RSI", "Pivot Points", "Volume Bars", "Bollinger Bands", "ATR", "MACD", "Stochastic", "OBV"

    Indicator explanation feature
        -uses calculated indicator values to create a simple technical summary
        -shows trend, momentum, VWAP position, pivot position, and volume confirmation

    -Local Ollama AI analysis (REPLACED WITH GROQ)
        -uses Ollama to analyze the stock indicators locally and summarize them 

    -Groq AI analysis
        -same prompt as Ollama indicator summary except it works online

    -Company data section
        -Market Cap, EPS, Sector, P/E, Suggested Benchmark feature, business summary, etc.

    -Company Data AI (Groq) Analysis Feature
        Summarizes all information from company data in a beginner friendly way
        -Answers in this format: Company overview, What Company does, Industry/Sector Context, ValuationCheck, Financial Strength, Growth/Profitability, Risk Factors, Suggested Benchmarks, Beginner Explanation
        -Separate AI section at the bottom of the web app which includes the Groq Analysis

    -Alternative option to select specific start/end date for data retrieval
        Makes it so users can customize what time period they see in order to allow them to track price movement from specific dates such as earnings

    AI chatbot assistant that helps users learn investing terms and concepts
        -has suggested questions so users have a better idea of what to ask
    
    New user guide that explains everything in the web app such as indicators or features
        -Located at the top of the web app, intended to better guide users through the features 
Next Features:
Improved AI analysis with more context like recent news and sector trends
    like a research assistant that you can feed specific data or ask to find specific data


Add beginner friendly explanations through the web app
AI analysis of recent news articles combined with indicator summary
Portfolio tracker


