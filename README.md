# 📊 Stock Market Performance Analyzer (SMPA)

Welcome to **SMPA – Stock Market Performance Analyzer**, a powerful and interactive Streamlit-based web app that helps users visualize, analyze, and monitor stock performance, risk, and financial trends using real-time data from Yahoo Finance and StockNews API.

---

## 🚀 Features

✅ User-friendly interface via Streamlit  
✅ Supports multiple stock tickers  
✅ Custom date range selection  
✅ Dynamic visualizations with Plotly  
✅ Price movement, volume, and trend analysis  
✅ Moving Averages (MA60/MA120 or custom)  
✅ Volatility and Risk-Adjusted Returns  
✅ Correlation between stocks  
✅ Live financial news sentiment  

---

## 🧠 Modules Covered

- 📈 **Historical Price Charts** (Line, Area)
- 📊 **Volume Trends** (Company-wise, Cumulative)
- 🔁 **Moving Averages** (customizable)
- ⚖️ **Volatility Index**
- 🔗 **Stock Correlation**
- 📰 **Top 10 News Articles with Sentiment Analysis**

---

## 🔧 Tech Stack

- **Python**
- **Streamlit** – frontend interface
- **Plotly Express & Graph Objects** – data visualization
- **yFinance** – real-time stock data
- **pandas, numpy** – data manipulation
- **stocknews** – news feed & sentiment
- **matplotlib** – auxiliary plots

---

## 🛠️ Installation

Make sure you have Python 3.8+ and pip installed.

```bash
# Clone the repository
git clone https://github.com/GirishRPardeshi/smpa.git
cd smpa

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```
---

## ▶️ Run the App
```bash
streamlit run SMPA.py
```
- Then open http://localhost:8501 in your browser.
