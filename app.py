import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json
import os

# --- PERSISTENCE LAYER (DATA TETAP AMAN) ---
CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            for key, value in data.items():
                st.session_state[key] = value

def save_config():
    data = {
        's_growth': st.session_state.s_growth,
        's_tactical': st.session_state.s_tactical,
        's_hedging': st.session_state.s_hedging,
        'assets_data': st.session_state.assets_data
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

# 1. Konfigurasi Halaman & UI Clean
st.set_page_config(page_title="Growth Blueprint V27", layout="wide")

if 'config_loaded' not in st.session_state:
    load_config()
    st.session_state.config_loaded = True

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
    
    /* LEBAR SIDEBAR: Dikunci 250px (2 spasi dari teks terpanjang) */
    section[data-testid="stSidebar"] {
        width: 250px !important;
        min-width: 250px !important;
    }

    .locked-weight {
        background-color: rgba(128, 128, 128, 0.05);
        padding: 8px 10px;
        border-radius: 6px;
        font-size: 15px;
        font-weight: bold;
        color: #0088ff;
        text-align: center;
        border: 1px solid rgba(128, 128, 128, 0.1);
        margin-top: 2px;
    }

    /* MENGHILANGKAN TOMBOL (+/-) BAWAAN */
    input[type="number"]::-webkit-outer-spin-button,
    input[type="number"]::-webkit-inner-spin-button {
        -webkit-appearance: none !important;
        margin: 0 !important;
        display: none !important;
    }

    /* Memaksa elemen agar tidak bertumpuk di HP */
    section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">📈 Maximum Growth Blueprint: AI-Energy</p>', unsafe_allow_html=True)

# 2. Inisialisasi State Default
if 's_growth' not in st.session_state: st.session_state.s_growth = 65
if 's_tactical' not in st.session_state: st.session_state.s_tactical = 20
if 's_hedging' not in st.session_state: st.session_state.s_hedging = 15

if 'assets_data' not in st.session_state:
    st.session_state.assets_data = {
        'Growth': ["NVDA", "VST", "PLTR"],
        'Tactical': ["TSM", "AMD"],
        'Hedging': ["GLD", "BTC"]
    }

# 3. Sidebar: Kontrol Utama
st.sidebar.header("Konfigurasi Portofolio")
cap_base = st.sidebar.number_input("Modal Awal (Basis)", value=65.0, step=1.0)
cap_target = st.sidebar.number_input("Target Capital Gain", value=100.0, step=1.0)
bench_ticker = st.sidebar.text_input("Benchmark", value="SPY").strip().upper()

st.sidebar.markdown("---")

def get_cluster_weights(assets, cluster_total):
    n = len(assets)
    if n == 0: return []
    decay = 0.5 
    raw = [decay ** i for i in range(n)]
    norm = np.array(raw) / sum(raw)
    return [round(val * cluster_total, 1) for val in norm]

final_assets = []
final_weights = []

def render_cluster(name, display_name, state_key):
    st.sidebar.header(display_name)
    
    # LOGIKA KUOTA OTOMATIS: Hitung sisa maksimal yang diizinkan
    keys = ['s_growth', 's_tactical', 's_hedging']
    other_keys = [k for k in keys if k != state_key]
    current_others_sum = sum(st.session_state[k] for k in other_keys)
    max_quota = 100 - current_others_sum
    
    st.sidebar.markdown(f"<p style='font-size:11px; color:#555555; margin-bottom:5px;'>Alokasi (Maks: {max_quota}%) &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Aset (➖/➕)</p>", unsafe_allow_html=True)
    
    c_alloc, c_min, c_plus = st.sidebar.columns([2.5, 1, 1])
    with c_alloc:
        # Menggunakan max_quota sebagai batas input
        st.number_input(f"alloc_{name}", min_value=0, max_value=max_quota, step=1, key=state_key, label_visibility="collapsed")
    with c_min:
        if st.button("➖", key=f"del_{name}"):
            if len(st.session_state.assets_data[name]) > 1:
                st.session_state.assets_data[name].pop()
                st.rerun()
    with c_plus:
        if st.button("➕", key=f"add_{name}"):
            st.session_state.assets_data[name].append("")
            st.rerun()
    
    current_assets = st.session_state.assets_data[name]
    c_weight_limit = st.session_state[state_key]
    w_list = get_cluster_weights(current_assets, c_weight_limit)

    for idx, asset in enumerate(current_assets):
        col_a, col_w = st.sidebar.columns([2, 1.5])
        with col_a:
            val = st.text_input(f"in_{name}_{idx}", value=asset, key=f"txt_{name}_{idx}", label_visibility="collapsed").upper()
            st.session_state.assets_data[name][idx] = val
        with col_w:
            st.markdown(f"<div class='locked-weight'>{w_list[idx]}% 🔒</div>", unsafe_allow_html=True)
        if val:
            final_assets.append(val)
            final_weights.append(w_list[idx])
    st.sidebar.markdown("---")

render_cluster('Growth', 'Growth Engine', 's_growth')
render_cluster('Tactical', 'Tactical Support', 's_tactical')
render_cluster('Hedging', 'Hedging & Defense', 's_hedging')

if st.sidebar.button("💾 SAVE CONFIGURATION", use_container_width=True):
    save_config()
    st.sidebar.success("Konfigurasi Terkunci!")

# 4. Komputasi Data
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
        if w_norm.sum() > 0: w_norm = w_norm / w_norm.sum()
            
        p_ret = rets[final_assets].dot(w_norm)
        b_ret = rets[bench_ticker]

        p_cum = (1 + p_ret).cumprod() * cap_base
        b_cum = (1 + b_ret).cumprod() * cap_base
        dd = (p_cum / p_cum.cummax()) - 1
        sharpe = ((p_ret.mean() - (0.04/252)) / p_ret.std()) * np.sqrt(252)
        alpha = (p_ret.mean() * 252) - (0.04 + (p_ret.cov(b_ret)/b_ret.var()) * ((b_ret.mean() * 252) - 0.04))

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
        with m2: st.markdown(kpi_box("Sharpe Ratio (Efficiency)", f"{sharpe:.2f}", "🔵 Baik" if sharpe > 1.5 else "🔴 Kurang", "🔴 <1.0 | 🟡 1.0-1.5 | 🔵 >1.5"), unsafe_allow_html=True)
        with m3: st.markdown(kpi_box("Alpha vs Benchmark", f"{alpha*100:.1f}%", "🔵 Baik" if alpha*100 > 5 else "🔴 Kurang", "🔴 <0% | 🟡 0-5% | 🔵 >5%"), unsafe_allow_html=True)
        with m4: st.markdown(kpi_box("Max Drawdown", f"{dd.min()*100:.2f}%", "🔵 Baik" if dd.min() > -0.15 else "🔴 Kurang", "🔵 >-15% | 🟡 -30% | 🔴 <-30%"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("Equity Curve")
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(x=p_cum.index, y=p_cum, name='Portfolio', line=dict(color='#0088ff', width=2.5)))
            fig1.add_trace(go.Scatter(x=b_cum.index, y=b_cum, name='S&P 500', line=dict(color='#333333', width=2)))
            fig1.add_hline(y=cap_target, line_dash="dot", line_color="#ff4b4b")
            fig1.update_layout(height=380, margin=dict(l=0,r=0,t=0,b=0), template="simple_white", legend=dict(orientation="h", y=1.1, x=0))
            # PERBAIKAN: staticPlot: True agar tidak bergerak saat disentuh
            st.plotly_chart(fig1, use_container_width=True, config={'staticPlot': True})
        with g2:
            st.subheader("Drawdown Map")
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=dd.index, y=dd, fill='tozeroy', line=dict(color='#ff4b4b', width=1)))
            fig2.update_layout(height=380, margin=dict(l=0,r=0,t=0,b=0), template="simple_white")
            # PERBAIKAN: staticPlot: True agar tidak bergerak saat disentuh
            st.plotly_chart(fig2, use_container_width=True, config={'staticPlot': True})
else:
    st.info("Lengkapi nama saham di tiap kluster untuk memulai.")
