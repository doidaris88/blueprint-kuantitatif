import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. Konfigurasi Halaman & Penghapusan Branding (Clean UI)
st.set_page_config(page_title="Blueprint Portofolio Kuantitatif", layout="wide")
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title("📈 Maximum Growth Blueprint: AI-Energy Nexus")

# 2. Panel Input Samping (Parameter Portofolio)
st.sidebar.header("Parameter Blueprint")
capital_base = st.sidebar.number_input("Modal Awal (Basis)", value=65.0, step=1.0)
capital_target = st.sidebar.number_input("Target Capital Gain", value=100.0, step=1.0)
benchmark_ticker = st.sidebar.text_input("Benchmark Ticker", value="SPY")

st.sidebar.subheader("Alokasi Aset & Bobot (%)")
col1, col2 = st.sidebar.columns(2)
with col1:
    asset1 = st.text_input("Aset 1", value="NVDA")
    asset2 = st.text_input("Aset 2", value="VST")
    asset3 = st.text_input("Aset 3 (Hedge)", value="GLD")
with col2:
    weight1 = st.number_input("Bobot 1", value=50.0, step=5.0)
    weight2 = st.number_input("Bobot 2", value=30.0, step=5.0)
    weight3 = st.number_input("Bobot 3", value=20.0, step=5.0)

weights = np.array([weight1, weight2, weight3]) / 100
tickers = [asset1, asset2, asset3]

# 3. Pengambilan Data dari Yahoo Finance
@st.cache_data
def get_data(tickers, benchmark):
    all_tickers = tickers + [benchmark]
    data = yf.download(all_tickers, period="3y", progress=False)['Close']
    return data

data = get_data(tickers, benchmark_ticker)
returns = data.pct_change().dropna()

# 4. Mesin Komputasi Metrik Kuantitatif
# Menghitung Return Portofolio Harian
port_returns = returns[tickers].dot(weights)
bench_returns = returns[benchmark_ticker]

# Menghitung Return Kumulatif
port_cum_returns = (1 + port_returns).cumprod() * capital_base
bench_cum_returns = (1 + bench_returns).cumprod() * capital_base

# Kalkulasi Metrik Vital
years = len(port_returns) / 252
cagr = ((port_cum_returns.iloc[-1] / capital_base) ** (1 / years)) - 1

# Volatilitas & Sharpe Ratio (Risk-Free Rate asumsi 4%)
risk_free_rate = 0.04 / 252
excess_returns = port_returns - risk_free_rate
sharpe_ratio = (excess_returns.mean() / port_returns.std()) * np.sqrt(252)

# Alpha (Annualized)
port_ann_return = (port_returns.mean() * 252)
bench_ann_return = (bench_returns.mean() * 252)
beta = port_returns.cov(bench_returns) / bench_returns.var()
alpha = port_ann_return - (0.04 + beta * (bench_ann_return - 0.04))

# Drawdown Calculation
roll_max = port_cum_returns.cummax()
drawdown = (port_cum_returns / roll_max) - 1
max_drawdown = drawdown.min()

# 5. Visualisasi Dasbor (Frontend)
st.markdown("---")
# Baris 1: KPI Utama
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Current Value vs Target", f"${port_cum_returns.iloc[-1]:.2f}", f"Target: ${capital_target}")
kpi2.metric("Sharpe Ratio (Efisiensi)", f"{sharpe_ratio:.2f}")
kpi3.metric("Alpha vs Benchmark", f"{alpha*100:.2f}%")
kpi4.metric("Max Drawdown", f"{max_drawdown*100:.2f}%")

st.markdown("---")

# Baris 2: Grafik Pertumbuhan Modal & Drawdown Map
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("Kurva Ekuitas vs Benchmark")
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=port_cum_returns.index, y=port_cum_returns, mode='lines', name='Portofolio', line=dict(color='#00ff00', width=2)))
    fig1.add_trace(go.Scatter(x=bench_cum_returns.index, y=bench_cum_returns, mode='lines', name=f'Benchmark ({benchmark_ticker})', line=dict(color='#888888', width=1.5)))
    fig1.add_hline(y=capital_target, line_dash="dash", line_color="red", annotation_text=f"Target ${capital_target}")
    fig1.update_layout(height=400, template="plotly_dark", margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig1, use_container_width=True)

with col_chart2:
    st.subheader("Peta Drawdown (Manajemen Risiko)")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=drawdown.index, y=drawdown, fill='tozeroy', mode='lines', name='Drawdown', line=dict(color='#ff4444', width=1)))
    fig2.update_layout(height=400, template="plotly_dark", yaxis_tickformat='.1%', margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig2, use_container_width=True)

