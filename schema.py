import streamlit as st
import yfinance as yf
import pandas as pd

st.title("📊 5-Day Stock Data Viewer with % Change")

tickers_input = st.text_input("Enter stock tickers (comma separated):", "AAPL, MSFT, GOOGL")

if st.button("Fetch Data"):
    tickers = [t.strip().upper() for t in tickers_input.split(',')]
    all_rows = []

    for ticker in tickers:
        try:
            df = yf.Ticker(ticker).history(period="5d")
            if not df.empty:
                df = df.reset_index()
                df["Ticker"] = ticker
                # Calculate percentage change on Close price
                df["Pct Change"] = df["Close"].pct_change() * 100
                # Round percentage change to 2 decimals for display
                df["Pct Change"] = df["Pct Change"].round(2)
                all_rows.append(df[["Ticker", "Date", "Open", "High", "Low", "Close", "Pct Change", "Volume"]])
            else:
                st.warning(f"No data found for {ticker}")
        except Exception as e:
            st.error(f"Error retrieving data for {ticker}: {e}")

    if all_rows:
        final_df = pd.concat(all_rows, ignore_index=True)
        st.dataframe(final_df)
    else:
        st.warning("No data available.")