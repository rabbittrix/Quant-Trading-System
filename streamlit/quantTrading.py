import streamlit as st
import pandas as pd
import numpy as np
import time
import random
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- HELPER FUNCTIONS ---

def generate_market_data(num_points=100):
    """Generates mock market data with random price fluctuations."""
    prices = np.cumsum(np.random.normal(0, 0.1, num_points)) + 100
    dates = pd.date_range(start="2024-01-01", periods=num_points, freq="1h")
    return pd.DataFrame({"Timestamp": dates, "Price": prices})

def generate_trading_signals(market_data):
    """Generates mock trading signals based on a simple moving average."""
    prices = market_data["Price"]
    short_ma = prices.rolling(window=5).mean()
    long_ma = prices.rolling(window=20).mean()
    signals = pd.Series(0, index=prices.index)
    signals[(short_ma > long_ma) & (short_ma.shift(1) <= long_ma.shift(1))] = 1  # Buy
    signals[(short_ma < long_ma) & (short_ma.shift(1) >= long_ma.shift(1))] = -1  # Sell
    return signals

def calculate_portfolio(market_data, signals, initial_capital=10000):
    """Calculates portfolio value based on signals and market data."""
    portfolio = [initial_capital]
    positions = 0
    cash = initial_capital
    for i in range(1, len(market_data)):
        if signals[i] == 1 and positions == 0:  # Buy if no position
            positions = cash / market_data["Price"][i]
            cash = 0
        elif signals[i] == -1 and positions != 0:  # Sell if holding
            cash = positions * market_data["Price"][i]
            positions = 0
        portfolio.append(cash + positions * market_data["Price"][i])
    return pd.DataFrame({"Portfolio": portfolio}, index=market_data.index)

def update_data(market_data, signals, portfolio_df):
    """Generates new mock data, signals, and portfolio value."""
    new_market_data = generate_market_data(1)
    combined_market_data = pd.concat([market_data.iloc[-20:], new_market_data], ignore_index=True)
    new_signals = generate_trading_signals(combined_market_data)
    new_portfolio = calculate_portfolio(pd.concat([market_data, new_market_data], ignore_index=True), pd.concat([signals, new_signals[-1:]], ignore_index=True))
    
    return new_market_data, new_signals.iloc[-1:], new_portfolio.iloc[-1:].Portfolio.iloc[0]

# --- STREAMLIT DASHBOARD ---

st.title("Quant Trading System Dashboard")

# Initialize Data
market_data_df = generate_market_data()
signals_series = generate_trading_signals(market_data_df)
portfolio_df = calculate_portfolio(market_data_df, signals_series)

# Display dataframes using streamlit
st.header("Market Data")
st.dataframe(market_data_df.head(5))

st.header("Trading Signals")
st.dataframe(signals_series.head(5))

st.header("Portfolio Value")
st.dataframe(portfolio_df.head(5))

# Create Plotly figure for live plotting
fig = make_subplots(rows=2, cols=1, subplot_titles=("Market Price", "Portfolio Value"))
fig.add_trace(go.Scatter(x=market_data_df["Timestamp"], y=market_data_df["Price"], mode="lines", name="Price"), row=1, col=1)
fig.add_trace(go.Scatter(x=portfolio_df.index, y=portfolio_df["Portfolio"], mode="lines", name="Portfolio"), row=2, col=1)
fig.update_layout(height=800) # Set height of the figure


st.plotly_chart(fig, use_container_width=True)

# Placeholder for live updates
live_update_text = st.empty()

# Update data in real-time
while True:
    new_market_data, new_signals, new_portfolio_value = update_data(market_data_df, signals_series, portfolio_df)

    # Update dataframes
    market_data_df = pd.concat([market_data_df, new_market_data], ignore_index=True)
    signals_series = pd.concat([signals_series, new_signals], ignore_index=True)
    portfolio_df = pd.concat([portfolio_df, pd.DataFrame({"Portfolio":[new_portfolio_value]}, index=[new_market_data.Timestamp.iloc[0]])], ignore_index=False)

    # Update graphs with new data
    fig.update_traces(x=market_data_df["Timestamp"], y=market_data_df["Price"], selector=dict(name="Price"), row=1, col=1)
    fig.update_traces(x=portfolio_df.index, y=portfolio_df["Portfolio"], selector=dict(name="Portfolio"), row=2, col=1)
    st.plotly_chart(fig, use_container_width=True)

    # Display updated data
    live_update_text.text(f"Last Update Time: {new_market_data.Timestamp.iloc[0]} | New Price: {new_market_data.Price.iloc[0]:.2f} | New Portfolio Value: {new_portfolio_value:.2f} | Signal: {new_signals.iloc[0]}")

    time.sleep(1) # Simulate real-time update interval