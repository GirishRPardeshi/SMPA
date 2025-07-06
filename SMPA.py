import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime
from stocknews import StockNews
import datetime as dt
import plotly.graph_objects as go
import plotly.subplots as sp

st.set_page_config(
    page_title="Stock_Analyzer",page_icon=":money_with_wings:"
    )

#---Initialize the seaaion state---
if 'stage' not in st.session_state:
    st.session_state.stage = 0

def set_stage(stage):
    st.session_state.stage = stage    


st.header("Stock Market Performance Analysis")
st.write("---")
st.sidebar.title('Stock Market Analyzer')

#---Take input from user---
stock_tickers = st.sidebar.text_input("Please enter the stock tickers (separated by commas): ")
from datetime import date, timedelta
start_date = st.sidebar.date_input("Start Date", value=date.today() - timedelta(days=90))
end_date = st.sidebar.date_input("End Date", value=date.today())

if start_date >= end_date:
    st.error("Start date must be before end date.")
    st.stop()

#---Get stock data---
tickers = [ticker.strip().upper() for ticker in stock_tickers.split(',') if ticker.strip()]
if not tickers:
    st.error("Please enter at least one valid stock ticker.")
    st.stop()
st.write("Tickers:", tickers)
st.write("Start:", start_date)
st.write("End:", end_date)

# Calculate the time difference between end and start dates
option1 = (end_date - start_date).days
option = "{} days".format(option1) if option1 > 0 else "Less than 1 day"
# Initialize an empty DataFrame to store the stock data
df = []

st.sidebar.button('Fetch Stock Data', on_click=set_stage, args=(1,))
if st.session_state.stage > 0:
    with st.spinner("Wait a Moment.."):
        
        # Fetch the stock data for each ticker and append it to the DataFrame
        for ticker in tickers:
            try:
                data = yf.download(ticker, start=start_date, end=end_date)
                if data.empty:
                    st.warning(f"No valid data fetched for ticker: {ticker}")
                    continue
                df.append(data)
            except Exception as e:
                st.write(f"Error fetching data for ticker {ticker}: {e}")
                continue
        if df:
            df= pd.concat(df, keys=tickers, names=['Ticker', 'Date'])

            # Reset the index of the DataFrame
            df = df.reset_index()
        else:
            df = pd.DataFrame()
        
        if not df.empty:
            # Create a new column that represents the percentage change from one day to another 
            df["Percent Change"] = ((df["Close"].diff()) / df["Close"]) * 100
            df = df.round(2)

            # Display the DataFrame with the added "Percent Change" column
            st.subheader("Stock Prices & Percentage Changes")
            left_column, right_column = st.columns([2, 1])
            with left_column:
                st.dataframe(df[['Ticker','Date','Open','High','Low','Close','Volume','Percent Change']])

            with right_column:
                st.markdown("""
                    **Key Indicators**

                - The "Percent Change" column shows the percent change in price from one day to the next.
                - A positive value indicates that the stock price increased during the period. 
                - while a negative value sign indicates that stock price decreased during the period.
                """)
            st.write("---")
        else:
            st.error("No data available to analyze. Please check ticker symbols or date range.")    

        # Show the analysis if the user clicks the "Show Analysis" button
        st.sidebar.button('Show Analysis', on_click=set_stage, args=(2,))
        if st.session_state.stage > 1:
            left_column, right_column = st.columns([3, 1])
            with left_column:
                    fig1 = px.line(df, x='Date', 
                        y='Close', color='Ticker',
                        labels={'Date':'Date', 'Close':'Closing Price', 'Ticker':'Company'}, 
                        title="Stock Market Performance for the Last " + option,
                        width=700,height=450)

                    st.plotly_chart(fig1)

            with right_column:
                    best_performing_ticker = df.loc[df.groupby('Date')['Close'].idxmax()]['Ticker']
                    st.write("##")
                    st.write("##")   
                    st.write(f"**Best Performing Company:** {best_performing_ticker.iloc[-1]}")
                    st.write(f"**Closing Price:** {df['Close'].loc[df['Ticker'] == best_performing_ticker.iloc[-1]].iloc[-1]:,.2f}")       
            st.write("---")
            
            with st.container():
                left_column, right_column = st.columns([2,1])
                with left_column:
                    fig = px.area(df, x='Date', y='Volume', color='Ticker',facet_col='Ticker',
                        labels={'Date':'Date', 'Close':'Closing Price', 'Ticker':'Company'},
                        title='Daily Volume of  Company')
                st.plotly_chart(fig)
                st.write("---")
            with st.container():
                left_column, right_column = st.columns([2,1])
                with left_column:
                    df_grouped = df.groupby(['Date','Ticker']).sum().unstack()
                    df_grouped.columns = df_grouped.columns.get_level_values(0) + '_' + df_grouped.columns.get_level_values(1)
                    df_grouped = df_grouped.reset_index().rename(columns={'Date': 'date'})
                    # Filter the DataFrame to only include numeric columns
                    df_numeric = df_grouped.select_dtypes(include=['float64', 'int64'])

                    # Create the figure using the filtered DataFrame
                    fig2 = px.area(df_numeric,
                                labels={'value':'Cumulative Volume'},
                                title="Daily Volume by Ticker",
                                height=380)

                    # Plot the figure
                    st.plotly_chart(fig2)

                with  right_column:
                    st.write("##")
                    st.markdown("""
                    **Key Indicators**

                    - The area chart displays the cumulative volume over time for each company.
                    """)
                st.write("---\n\n")
                   

            #Creating Separate tabs        
            pricing_data,MA,Volatility,Correlation,news=st.tabs(["Pricing  Data","Moving  Average", "Volatility Index","Correlation","Top News"])
            with pricing_data:
                st.header("Price Movements")
                df2=df
                df2['% Change']=df['Adj Close']/df['Adj Close'].shift(1)-1
                df2.dropna(inplace=True)
                for ticker in tickers:
                    left_column,right_column=st.columns([2,1])
                    with  left_column:
                        st.write("Pricing data of",ticker)
                        df3=df2[df2['Ticker']==ticker]
                        st.write(df3)

                        # Calculate monthly and weekly returns
                        monthly_return = df3['% Change'].rolling(window=21).mean()  # Assuming 21 trading days in 1 months
                        weekly_return = df3['% Change'].rolling(window=10).mean()   # Assuming 5 trading days in 1 weeks

                        # Add monthly and weekly returns to the DataFrame
                        df3['Monthly Return'] = monthly_return
                        df3['Weekly Return'] = weekly_return

                    with right_column:
                        st.write("##")  
                        annual_return = df3['% Change'].mean()*252*100
                        st.write('Annual Returns of',ticker,' is ',annual_return,'%')

                        stdev=np.std(df3['% Change'])*np.sqrt(252)
                        st.write('Standard Deviation of',ticker,' is ',stdev*100,'%')
                        st.write('Risk Adj. Return of',ticker,'is',annual_return/(stdev*100))
                        
                       

                    left_column,right_column=st.columns([1,1])
                    with  left_column:
                            monthly_return_1 = df3['Monthly Return'].tail(1).values[0] * 100
                            monthly_return_2 = df3['Monthly Return'].tail(2).values[0] * 100
                            monthly_return_3 = df3['Monthly Return'].tail(3).values[0] * 100
                            st.write('Last Month Monthly Return of ',ticker,'is', monthly_return_1,'%')
                            st.write('2 Months Ago Monthly Return of ',ticker,' is ',monthly_return_2,'%')
                            st.write('3 Months Ago Monthly Return of ',ticker,' is ',monthly_return_3,'%')

                    with right_column:
                            weekly_return_1 = df3['Weekly Return'].tail(1).values[0] * 100
                            weekly_return_2 = df3['Weekly Return'].tail(2).values[0] * 100
                            weekly_return_3 = df3['Weekly Return'].tail(3).values[0] * 100

                            st.write('Last Week Weekly Return of ',ticker,' is ',weekly_return_1,'%')
                            st.write('2 Weeks Ago Weekly Return of ',ticker,' is ',weekly_return_2,'%')
                            st.write('3 Weeks Ago Weekly Return of ',ticker,' is', weekly_return_3,'%')

                    st.write('----')     
    
            with MA:
                input1 = st.number_input("Enter the number of days for the first moving average", min_value=1, value=60)
                input2 = st.number_input("Enter the number of days for the second moving average", min_value=1, value=120)

                with st.container():
                    df['MA1'] = df.groupby('Ticker')['Close'].rolling(window=input1).mean().reset_index(0, drop=True)
                    df['MA2'] = df.groupby('Ticker')['Close'].rolling(window=input2).mean().reset_index(0, drop=True)

                    st.subheader("Dataset with Moving Averages")
                    st.write(df)

                    for ticker, group in df.groupby('Ticker'):
                        fig3 = go.Figure()

                        fig3.add_trace(go.Scatter(x=group['Date'], y=group['Close'], mode='lines', name=f"{ticker} Close Price"))
                        fig3.add_trace(go.Scatter(x=group['Date'], y=group['MA1'], mode='lines', name=f"{ticker} MA{input1}"))
                        fig3.add_trace(go.Scatter(x=group['Date'], y=group['MA2'], mode='lines', name=f"{ticker} MA{input2}"))

                        fig3.update_layout(title=f"{ticker} Moving Averages", xaxis_title='Date', yaxis_title='Stock Price')
                        #Plot all stocks MA
                        st.plotly_chart(fig3)
                    st.write("---")
            
            with Volatility:
                with st.container():
                    df['Volatility'] = df.groupby('Ticker')['Close'].pct_change().rolling(window=10).std().reset_index(0, drop=True)

                    st.subheader("Dataset with Stocks Volatility")
                    st.write(df)

                    fig4 = px.line(df, x='Date', y='Volatility', 
                        color='Ticker', 
                        title='Volatility of All Companies')
                    st.plotly_chart(fig4)
                    st.write("---")

            with Correlation:
                with st.container():
                    if len(tickers)>1:
                        # Correlation calculation and plotting
                        correlation = df.groupby('Ticker')['Close'].rolling(window=10).corr()
                        correlation_df = pd.DataFrame(correlation).reset_index()

                        # Filter out non-numeric stocks (like Apple and Microsoft)
                        correlation_df = correlation_df[correlation_df['Ticker'].isin(tickers)]

                        # Create a DataFrame with the stock prices of the specified stocks
                        stock_data = df.loc[df['Ticker'].isin(tickers), ['Date', 'Close', 'Ticker']]
                        stock_data = stock_data.pivot(index='Date', columns='Ticker', values='Close').reset_index()

                        # Create a scatter plot to visualize the correlation for the specified stocks
                        if len(tickers)>=2:
                            fig5 = px.scatter(stock_data, x=tickers[0], y=tickers[1], 
                            trendline='ols', title='Correlation between Stock Prices')
                            st.plotly_chart(fig5)

                        if len(tickers)>=4:
                            fig6 = px.scatter(stock_data, x=tickers[2], y=tickers[3], 
                            trendline='ols',  title='Correlation between Stock Prices')
                            st.plotly_chart(fig6)
                    else:
                        st.write("Please input more than one stock ticker to view the correlation between them.")        
                    st.write("---") 
            with news:
                with st.container():
                        st.header("Top 10 News in US Stock Market")
                        sn = StockNews(ticker, save_news=False)
                        df_news= sn.read_rss()
                        for i in range(10):
                            st.subheader(f'News {i+1}')
                            st.write(df_news['published'][i])
                            st.write(df_news['title'] [i])
                            st.write(df_news['summary'][i])
                            title_sentiment = df_news['sentiment_title'][i]
                            st.write(f'Title Sentiment {title_sentiment}')
                            news_sentiment = df_news['sentiment_summary'][i]
                            st.write(f'News Sentiment {news_sentiment}')
                            st.write("---")
        if st.session_state.stage > 1:
            st.write('The end')
            st.sidebar.button('Reset', on_click=set_stage, args=(0,))
