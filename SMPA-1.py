import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import yfinance as yf
import streamlit as st
from datetime import datetime
from stocknews import StockNews
import datetime as dt
import plotly.graph_objects as go
import plotly.subplots as sp

st.set_page_config(page_title="GAnalyzer", page_icon=":money_with_wings:")

if 'stage' not in st.session_state:
    st.session_state.stage = 0

def set_stage(stage):
    st.session_state.stage = stage

st.header("Stock Market Performance Analysis")
st.write("---")
st.sidebar.title('Stock Market Analyzer')

try:
    tickers_input = st.sidebar.text_input("Please enter the stock tickers (separated by commas): ", "AAPL, MSFT")
    start = st.sidebar.date_input("Start Date", value=datetime.now() - pd.DateOffset(months=3))
    end = st.sidebar.date_input("End Date", value=datetime.now())
except ValueError:
    st.write("Invalid input. Please enter a string of tickers separated by commas.")

tickers = [t.strip().upper() for t in tickers_input.split(',')]
option1 = (end - start).days
option = f"{option1} days" if option1 > 0 else "Less than 1 day"

st.sidebar.button('Fetch Stock Data', on_click=set_stage, args=(1,))

if st.session_state.stage > 0:
    with st.spinner("Wait a Moment.."):
        all_rows = []
        for ticker in tickers:
            df = yf.Ticker(ticker).history(start=start, end=end)
            if not df.empty:
                df = df.reset_index()
                df['Ticker'] = ticker
                df['Percent Change'] = df['Close'].pct_change() * 100
                df = df.round(2)
                all_rows.append(df[['Ticker', 'Date', 'Open', 'High', 'Low', 'Close', 'Percent Change', 'Volume']])
        if all_rows:
            df = pd.concat(all_rows, ignore_index=True)
            st.subheader("Stock Prices & Percentage Changes")
            left_column, right_column = st.columns([2, 1])
            with left_column:
                st.dataframe(df)
            with right_column:
                st.markdown("""
                    **Key Indicators**

                - The "Percent Change" column shows the percent change in price from one day to the next.
                - A positive value indicates that the stock price increased during the period. 
                - while a negative value sign indicates that stock price decreased during the period.
                """)
        else:
            st.warning("No data available.")


        # Show the analysis if the user clicks the "Show Analysis" button
        st.sidebar.button('Show Analysis', on_click=set_stage, args=(2,))
        if st.session_state.stage > 1:
            left_column, right_column = st.columns([2, 1])
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
                    st.write(f"**Closing Price:** ${df['Close'].loc[df['Ticker'] == best_performing_ticker.iloc[-1]].iloc[-1]:,.2f}")       
            st.write("---")
            
            with st.container():
                left_column, right_column = st.columns([2,1])
                with left_column:
                    fig = px.area(df, x='Date', y='Close', color='Ticker',facet_col='Ticker',
                        labels={'Date':'Date', 'Close':'Closing Price', 'Ticker':'Company'},
                        title='Daily Closing prices of Company')
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
                df2['% Change']=df['Close']/df['Close'].shift(1)-1
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
                with st.container():
                    df['MA100'] = df.groupby('Ticker')['Close'].rolling(window=100).mean().reset_index(0, drop=True)
                    df['MA200'] = df.groupby('Ticker')['Close'].rolling(window=200).mean().reset_index(0, drop=True)

                    st.subheader("Dataset with Moving Averages")
                    st.write(df)

                    for ticker, group in df.groupby('Ticker'):
                        fig3 = go.Figure()

                        fig3.add_trace(go.Scatter(x=group['Date'], y=group['Close'], mode='lines', name=f"{ticker} Close Price"))
                        fig3.add_trace(go.Scatter(x=group['Date'], y=group['MA100'], mode='lines', name=f"{ticker} MA100"))
                        fig3.add_trace(go.Scatter(x=group['Date'], y=group['MA200'], mode='lines', name=f"{ticker} MA200"))

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
                    st.write("---") 
            with news:
                with st.container():
                    for ticker in tickers:
                        st.header(f'News of {ticker}')
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