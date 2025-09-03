import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from stocknews import StockNews
from datetime import datetime

st.set_page_config(page_title="SMPA - Load to Analyse", page_icon=":bar_chart:", layout='wide')

# ---------------------- Helpers & Caching ----------------------
@st.cache_data(show_spinner=False)
def fetch_ticker_history(ticker: str, start: str, end: str) -> pd.DataFrame:
    try:
        df = yf.Ticker(ticker).history(start=start, end=end, auto_adjust=False)
    except Exception:
        df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=False)

    if df is None or df.empty:
        return pd.DataFrame()

    df = df.reset_index()
    df['Ticker'] = ticker.upper()
    df = df.rename(columns={'Adj Close': 'Adj_Close'})
    return df[['Ticker', 'Date', 'Open', 'High', 'Low', 'Close', 'Adj_Close', 'Volume']]


def compute_compound_return(series: pd.Series) -> float:
    return (np.prod(1 + series.dropna()) - 1) if len(series.dropna()) > 0 else np.nan


def rolling_compound(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window).apply(lambda x: np.prod(1 + x) - 1, raw=True)


# ---------------------- UI Inputs ----------------------
st.sidebar.title("SMPA - Stock Market Performance Analyzer")

tickers_input = st.sidebar.text_input("Enter tickers (comma separated)", value="AAPL, MSFT")
start_date = st.sidebar.date_input("Start date", value=datetime.now().date() - pd.DateOffset(months=3))
end_date = st.sidebar.date_input("End date", value=datetime.now().date())

fetch_btn = st.sidebar.button("Fetch Stock Data")
reset_btn = st.sidebar.button("Reset")

if reset_btn:
    for k in list(st.session_state.keys()):
        st.session_state.pop(k)

tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]

if fetch_btn:
    st.session_state['fetched'] = True

if not st.session_state.get('fetched'):
    st.header("Welcome — load stock data to begin")
    st.write("Enter tickers and press `Fetch Stock Data`. For Indian NSE tickers add `.NS` (eg: RELIANCE.NS)")
    st.stop()

# ---------------------- Data Fetching ----------------------
with st.spinner("Downloading data — one sec..."):
    frames = []
    for t in tickers:
        df_t = fetch_ticker_history(t, str(start_date), str(end_date))
        if not df_t.empty:
            frames.append(df_t)

    if not frames:
        st.warning("No data fetched for the provided tickers/date range.")
        st.stop()

    df = pd.concat(frames, ignore_index=True)

# ensure correct ordering
df = df.sort_values(['Ticker', 'Date']).reset_index(drop=True)

# ---------------------- Derived columns ----------------------
df['Return'] = df.groupby('Ticker')['Adj_Close'].pct_change()
df['Pct_Change'] = (df['Return'] * 100).round(4)

period_returns = df.groupby('Ticker').apply(lambda g: (g['Adj_Close'].iloc[-1] / g['Adj_Close'].iloc[0]) - 1 if len(g) >= 2 else np.nan)
period_returns = period_returns.rename('Period_Return')

# FIX: use transform so index matches df
df['Weekly_Return'] = df.groupby('Ticker')['Return'].transform(lambda s: rolling_compound(s, window=5))
df['Monthly_Return'] = df.groupby('Ticker')['Return'].transform(lambda s: rolling_compound(s, window=21))

# Volatility
df['Volatility_10d'] = df.groupby('Ticker')['Return'].transform(lambda s: s.rolling(window=10).std())

# Moving averages
df['MA50'] = df.groupby('Ticker')['Close'].transform(lambda s: s.rolling(window=50).mean())
df['MA200'] = df.groupby('Ticker')['Close'].transform(lambda s: s.rolling(window=200).mean())

# ---------------------- Top bar / summary ----------------------
st.title("Stock Market Performance Analysis —")
st.write(f"Date range: **{start_date}** → **{end_date}**")

best = period_returns.idxmax()
best_value = period_returns.max()
col1, col2, col3 = st.columns(3)
col1.metric("Tickers analyzed", len(tickers))
col2.metric("Best performer (total return)", best if pd.notna(best) else "—", f"{best_value:.2%}" if pd.notna(best_value) else "—")
col3.metric("Days in range", (end_date - start_date).days)

st.markdown("---")

# ---------------------- Main charts ----------------------
left, right = st.columns([3,1])
with left:
    fig = px.line(df, x='Date', y='Close', color='Ticker', title='Closing Prices')
    st.plotly_chart(fig, use_container_width=True)

with right:
    summary = df.groupby('Ticker').agg(
        start_price=('Close', 'first'),
        end_price=('Close', 'last'),
        period_return=('Ticker', lambda s: period_returns.loc[s.name]),
        avg_daily_return=('Return', 'mean'),
        vol_10d=('Volatility_10d', 'mean')
    )
    st.dataframe(summary.style.format({
        'start_price': '{:.2f}',
        'end_price': '{:.2f}',
        'period_return': '{:.2%}',
        'avg_daily_return': '{:.4f}',
        'vol_10d': '{:.4f}'
    }))

st.markdown("---")

# Volume area
vol_pivot = df.pivot(index='Date', columns='Ticker', values='Volume')
fig_vol = px.area(vol_pivot.reset_index(), x='Date', y=vol_pivot.columns, title='Daily Volume by Ticker')
st.plotly_chart(fig_vol, use_container_width=True)

st.markdown("---")

# ---------------------- Tabs ----------------------
pricing_tab, ma_tab, vol_tab, corr_tab, news_tab = st.tabs(["Pricing Data", "Moving Average", "Volatility", "Correlation", "Top News"])

with pricing_tab:
    st.header("Pricing & Returns")
    ticker_sel = st.selectbox("Choose ticker to inspect", tickers)
    df_t = df[df['Ticker'] == ticker_sel].copy()
    st.dataframe(df_t[['Date', 'Close', 'Adj_Close', 'Pct_Change', 'Weekly_Return', 'Monthly_Return']].tail(250), use_container_width=True)

    mean_daily = df_t['Return'].mean()
    ann_return = mean_daily * 252
    ann_vol = df_t['Return'].std() * np.sqrt(252)
    sharpe_approx = ann_return / ann_vol if ann_vol != 0 else np.nan
    st.write(f"Annualized return (approx): {ann_return:.2%}")
    st.write(f"Annualized vol (approx): {ann_vol:.2%}")
    st.write(f"Sharpe-like (rf≈0): {sharpe_approx:.2f}")

    latest_weekly = df_t['Weekly_Return'].dropna().iloc[-1]
    latest_monthly = df_t['Monthly_Return'].dropna().iloc[-1]

    st.write("Latest Weekly Return:", f"{latest_weekly:.2%}")
    st.write("Latest Monthly Return:", f"{latest_monthly:.2%}")

with ma_tab:
    st.header("Moving Averages")

    # Let user choose MA windows
    ma_options = st.multiselect(
        "Select Moving Average windows (in days)",
        options=[20, 50, 100, 200],
        default=[50, 200]
    )

    for ticker, grp in df.groupby('Ticker'):
        fig_ma = go.Figure()
        fig_ma.add_trace(go.Scatter(x=grp['Date'], y=grp['Close'], name='Close'))

        # add chosen MAs dynamically
        for window in ma_options:
            ma_col = f"MA{window}"
            if ma_col not in grp.columns:
                df[ma_col] = df.groupby('Ticker')['Close'].transform(lambda s: s.rolling(window=window).mean())
                grp = df[df['Ticker'] == ticker]
            fig_ma.add_trace(go.Scatter(x=grp['Date'], y=grp[ma_col], name=f"MA{window}"))

        fig_ma.update_layout(title=f"{ticker} - Moving Averages", xaxis_title='Date', yaxis_title='Price')
        st.plotly_chart(fig_ma, use_container_width=True)


with vol_tab:
    st.header("Volatility")
    fig_v = px.line(df, x='Date', y='Volatility_10d', color='Ticker', title='10-day Realized Volatility')
    st.plotly_chart(fig_v, use_container_width=True)

with corr_tab:
    st.header("Returns Correlation")
    returns_pivot = df.pivot(index='Date', columns='Ticker', values='Return')
    corr = returns_pivot.corr()
    fig_corr = px.imshow(corr, text_auto=True, title='Correlation Matrix of Daily Returns')
    st.plotly_chart(fig_corr, use_container_width=True)

    if len(tickers) >= 2:
        x_t, y_t = tickers[0], tickers[1]
        scatter_df = returns_pivot[[x_t, y_t]].dropna()
        fig_sc = px.scatter(scatter_df, x=x_t, y=y_t, title=f'Returns Scatter: {x_t} vs {y_t}')
        st.plotly_chart(fig_sc, use_container_width=True)

with news_tab:
    st.header("Top News (per ticker)")
    max_items = st.slider("Articles per ticker", min_value=1, max_value=10, value=3)
    for t in tickers:
        st.subheader(t)
        try:
            sn = StockNews(t, save_news=False)
            news_df = sn.read_rss()
            if news_df is None or news_df.empty:
                st.write("No news found")
                continue
            for i, row in news_df.head(max_items).iterrows():
                st.markdown(f"**{row.get('title', '')}**")
                st.write(row.get('published', ''))
                st.write(row.get('summary', ''))
                st.write(f"Title sentiment: {row.get('sentiment_title', '')} — Summary sentiment: {row.get('sentiment_summary', '')}")
                st.write('---')
        except Exception as e:
            st.write(f"Failed fetching news for {t}: {e}")

st.markdown('---')
if st.button('Download cleaned dataset (CSV)'):
    csv = df.to_csv(index=False)
    st.download_button('Download CSV', data=csv, file_name='smpa_clean.csv', mime='text/csv')

st.write('Done — cleaned and merged version running.')
