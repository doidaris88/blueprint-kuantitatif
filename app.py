import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. Konfigurasi Halaman & UI Clean
st.set_page_config(page_title="Growth Blueprint V18", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    input[type=text] { text-transform: uppercase; }
    .main-title {
        font-size: 36px !important; 
        font-weight: bold;
        margin-bottom: 25px;
        letter-spacing: -1px;
    }
    .cluster-tag {
        font-size: 11px;
        font-weight: bold;
        padding: 2px 8px;
        border-radius: 10px;
        margin-bottom: 10px;
        display: inline-block;
    }
    .locked-weight {
        background-color: #f8f9fa;
        padding: 8px 10px;
        border-radius: 6px;
        font-size: 15px;
        font-weight: bold;
        color: #0088ff;
        text-align: center;
        border: 1px solid #eeeeee;
        margin-top: 2px;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">📈 Maximum Growth Blueprint: AI-Energy</p>', unsafe_allow_html=True)

# 2. Sidebar: Kontrol Makro & Target
st.sidebar.header("Konfigurasi Portofolio")
cap_base = st.sidebar.number_input("Modal Awal (Basis)", value=65.0)
cap_target = st.sidebar.number_input("Target Capital Gain", value=100.0)
bench_ticker = st.sidebar.text_input("Benchmark", value="SPY").strip().upper()

st.sidebar.markdown("---")
st.sidebar.header("⚖️ Target Alokasi Kluster (%)")
# User bisa menyesuaikan besaran cluster, tapi total harus 100
c_growth = st.sidebar.slider("1. Growth Engine", 50, 80, 65)
c_tactical = st.sidebar.slider("2. Tactical Support", 5, 30, 20)
c_hedging = st.sidebar.slider("3. Hedging & Defense", 5, 25, 15)

total_check = c_growth + c_tactical + c_hedging
if total_check != 100:
    st.sidebar.warning(f"Total: {total_check}% (Harus 100%)")

st.sidebar.markdown("---")

# State Manajemen Aset per Kluster
if 'assets_data' not in st.session_state:
    st.session_state.assets_data = {
        'Growth': ["NVDA", "VST", "PLTR"],
        'Tactical': ["TSM", "AMD"],
        'Hedging': ["GLD", "BTC"]
    }

# Fungsi Pembagi Bobot Internal Kluster (Hierarki)
def get_cluster_weights(assets, cluster_total):
    n = len(assets)
    if n == 0: return []
    decay = 0.5 # Penurunan tajam untuk Growth Engine
    raw = [decay ** i for i in range(n)]
    norm = np.array(raw) / sum(raw)
    return [round(val * cluster_total, 1) for val in norm]

# UI Input per Kluster
final_assets = []
final_weights = []

def render_cluster(name, color):
    st.sidebar.markdown(f'<span class="cluster-tag" style="background-color: {color}22; color: {color}; border: 1px solid {color}55;">{name.upper()}</span>', unsafe_allow_html=True)
    current_assets = st.session_state.assets_data[name]
    
    # Tombol Tambah/Hapus per Kluster
    col_t1, col_t2 = st.sidebar.columns(2)
    if col_t1.button(f"+ {name}", key=f"add_{name}"):
        st.session_state.assets_data[name].append("")
        st.rerun()
    if col_t2.button(f"- {name}", key=f"del_{name}"):
        if len(current_assets) > 1:
            st.session_state.assets_data[name].pop()
            st.rerun()

    # Hitung bobot otomatis
    c_weight_limit = c_growth if name == 'Growth' else c_tactical if name == 'Tactical' else c_hedging
    w_list = get_cluster_weights(current_assets, c_weight_limit)
    
    for idx, asset in enumerate(current_assets):
        col_a, col_w = st.sidebar.columns([2, 1.5])
        with col_a:
            new_val = st.text_input(f"t_{name}_{idx}", value=asset, key=f"in_{name}_{idx}", label_visibility="collapsed").strip().upper()
            st.session_state.assets_data[name][idx] = new_val
        with col_w:
            st.markdown(f"<div class='locked-weight'>{w_list[idx]}% 🔒</div>", unsafe_allow_html=True)
        if new_val:
            final_assets.append(new_val)
            final_weights.append(w_list[idx])

render_cluster('Growth', '#0088ff')
render_cluster('Tactical', '#ffaa00')
render_cluster('Hedging', '#00cc66')

# 3. Komputasi Data
@st.cache_data(ttl=3600)
def fetch_data(tickers, benchmark):
    all_t = list(set([t for t in tickers if t] + [benchmark]))
    try:
        data = yf.download(all_t, period="3y", progress=False)['Close']
        return data.ffill()
    except: return pd.DataFrame()

df = fetch_data(final_assets, bench_ticker)

if not df.empty and all(a in df.columns for a in final_assets) and bench_ticker in df.columns:
    df_clean = df[final_assets + [bench_ticker]].dropna()
    if not df_clean.empty:
        rets = df_clean.pct_change().dropna()
        w_norm = np.array(final_weights) / 100
        p_ret = rets[final_assets].dot(w_norm)
        b_ret = rets[bench_ticker]

        p_cum = (1 + p_ret).cumprod() * cap_base
        b_cum = (1 + b_ret).cumprod() * cap_base
        dd = (p_cum / p_cum.cummax()) - 1
        sharpe = ((p_ret.mean() - (0.04/252)) / p_ret.std()) * np.sqrt(252)
        alpha = (p_ret.mean() * 252) - (0.04 + (p_ret.cov(b_ret)/b_ret.var()) * ((b_ret.mean() * 252) - 0.04))

        # Status Logic
        s_n = "🔵 Baik" if sharpe > 1.5 else "🟡 Sedang" if sharpe >= 1.0 else "🔴 Kurang"
        a_n = "🔵 Baik" if alpha*100 > 5 else "🟡 Sedang" if alpha*100 >= 0 else "🔴 Kurang"
        d_n = "🔵 Baik" if dd.min() >= -0.15 else "🟡 Sedang" if dd.min() >= -0.30 else "🔴 Kurang"

        def kpi_box(label, val, status, legend):
            return f"""
            <div style="background-color: #ffffff; padding: 18px; border-radius: 10px; border: 1px solid #eeeeee; height: 100%;">
                <div style="color: #555555; font-size: 14px; margin-bottom: 8px;">{label}</div>
                <div style="display: flex; align-items: baseline;">
                    <div style="font-size: 34px; font-weight: 500; color: #222222;">{val}</div>
                    <div style="font-size: 14px; margin-left: 12px; font-weight: 500; color: #666666;">{status}</div>
                </div>
                <div style="font-size: 11px; color: #999999; margin-top: 12px; border-top: 1px solid #f0f0f0; padding-top: 8px;">{legend}</div>
            </div>"""

        st.markdown("---")
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(kpi_box("Current Value vs Target", f"${p_cum.iloc[-1]:.2f}", "🎯 Target", f"Basis: ${cap_base:.0f} → Target: ${cap_target:.0f}"), unsafe_allow_html=True)
        with m2: st.markdown(kpi_box("Sharpe Ratio (Efficiency)", f"{sharpe:.2f}", s_n, "🔴 <1.0 | 🟡 1.0-1.5 | 🔵 >1.5"), unsafe_allow_html=True)
        with m3: st.markdown(kpi_box("Alpha vs Benchmark", f"{alpha*100:.1f}%", a_n, "🔴 <0% | 🟡 0-5% | 🔵 >5%"), unsafe_allow_html=True)
        with m4: st.markdown(kpi_box("Max Drawdown", f"{dd.min()*100:.2f}%", d_n, "🔵 >-15% | 🟡 -30% | 🔴 <-30%"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("Equity Curve")
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(x=p_cum.index, y=p_cum, name='Portfolio', line=dict(color='#0088ff', width=2.5)))
            fig1.add_trace(go.Scatter(x=b_cum.index, y=b_cum, name=f'S&P 500 ({bench_ticker})', line=dict(color='#333333', width=2)))
            fig1.add_hline(y=cap_target, line_dash="dot", line_color="#ff4b4b")
            fig1.update_layout(height=380, margin=dict(l=0,r=0,t=0,b=0), xaxis=dict(fixedrange=True), yaxis=dict(fixedrange=True), template="simple_white", legend=dict(orientation="h", y=1.1, x=0))
            st.plotly_chart(fig1, use_container_width=True, config={'staticPlot': True})
        with g2:
            st.subheader("Drawdown Map")
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=dd.index, y=dd, fill='tozeroy', line=dict(color='#ff4b4b', width=1)))
            fig2.update_layout(height=380, margin=dict(l=0,r=0,t=0,b=0), xaxis=dict(fixedrange=True), yaxis=dict(fixedrange=True, tickformat='.1%'), template="simple_white")
            st.plotly_chart(fig2, use_container_width=True, config={'staticPlot': True})
else:
    st.info("Lengkapi Ticker di Sidebar untuk memproses Blueprint...")
