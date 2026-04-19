import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. Konfigurasi Halaman & UI Clean
st.set_page_config(page_title="Growth Blueprint V24", layout="wide")

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
        color: #111111;
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

    /* 1. MENGHILANGKAN TOMBOL (+/-) BAWAAN KOTAK ANGKA SECARA TOTAL */
    input[type="number"]::-webkit-outer-spin-button,
    input[type="number"]::-webkit-inner-spin-button {
        -webkit-appearance: none !important;
        margin: 0 !important;
        display: none !important;
    }
    input[type="number"] {
        -moz-appearance: textfield !important;
    }

    /* 2. MEMAKSA KOLOM SIDEBAR TETAP HORIZONTAL DI HP (TIDAK BERTUMPUK KE BAWAH) */
    section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        flex-direction: row !important;
    }
    section[data-testid="stSidebar"] div[data-testid="column"] {
        min-width: 0 !important; 
    }

    /* 3. Merapikan tinggi tombol agar simetris dengan kotak input */
    .stButton > button {
        height: 39px !important;
        padding: 0px !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">📈 Maximum Growth Blueprint: AI-Energy</p>', unsafe_allow_html=True)

# 2. State Manajemen
if 's_growth' not in st.session_state: st.session_state.s_growth = 65
if 's_tactical' not in st.session_state: st.session_state.s_tactical = 20
if 's_hedging' not in st.session_state: st.session_state.s_hedging = 15

if 'assets_data' not in st.session_state:
    st.session_state.assets_data = {
        'Growth': ["NVDA", "VST", "PLTR"],
        'Tactical': ["TSM", "AMD"],
        'Hedging': ["GLD", "BTC"]
    }

# 3. Sidebar: Kontrol Modal Dasar
st.sidebar.header("Konfigurasi Portofolio")
cap_base = st.sidebar.number_input("Modal Awal (Basis)", value=65.0, step=1.0)
cap_target = st.sidebar.number_input("Target Capital Gain", value=100.0, step=1.0)
bench_ticker = st.sidebar.text_input("Benchmark", value="SPY").strip().upper()

st.sidebar.markdown("---")

# 4. Fungsi Hierarki Internal Kluster
def get_cluster_weights(assets, cluster_total):
    n = len(assets)
    if n == 0: return []
    decay = 0.5 
    raw = [decay ** i for i in range(n)]
    norm = np.array(raw) / sum(raw)
    return [round(val * cluster_total, 1) for val in norm]

# 5. Sidebar: Area Input Terpusat & Terbuka
final_assets = []
final_weights = []

def render_open_cluster(name, display_name, state_key):
    # Header Kluster (Sama persis dengan Konfigurasi Portofolio)
    st.sidebar.header(display_name)
    
    # Label Atas yang Presisi
    st.sidebar.markdown("""
    <div style='display: flex; justify-content: space-between; font-size: 13px; color: #555555; margin-bottom: 2px;'>
        <div style='flex: 2.2;'>Target Alokasi (%)</div>
        <div style='flex: 1.8; text-align: center;'>Aset (➖ / ➕)</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Baris 1: Dipecah 3 Kolom tapi dipaksa CSS tetap 1 baris di HP [ Input | - | + ]
    c_alloc, c_min, c_plus = st.sidebar.columns([2.2, 0.9, 0.9])
    
    with c_alloc:
        st.number_input(f"alloc_{name}", min_value=0, max_value=100, step=1, key=state_key, label_visibility="collapsed")
    with c_min:
        if st.button("➖", key=f"del_{name}", use_container_width=True, help="Hapus Aset Bawah"):
            if len(st.session_state.assets_data[name]) > 1:
                st.session_state.assets_data[name].pop()
                st.rerun()
    with c_plus:
        if st.button("➕", key=f"add_{name}", use_container_width=True, help="Tambah Aset"):
            st.session_state.assets_data[name].append("")
            st.rerun()
    
    # Baris 2: List Aset Langsung Muncul di Bawahnya
    current_assets = st.session_state.assets_data[name]
    c_weight_limit = st.session_state[state_key]
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
            
    st.sidebar.markdown("---")

# Render ke-3 Kluster Utama
render_open_cluster('Growth', 'Growth Engine', 's_growth')
render_open_cluster('Tactical', 'Tactical Support', 's_tactical')
render_open_cluster('Hedging', 'Hedging & Defense', 's_hedging')

# Validasi Total Alokasi 100%
total_check = st.session_state.s_growth + st.session_state.s_tactical + st.session_state.s_hedging
if total_check != 100:
    st.sidebar.error(f"⚠️ Total Alokasi Kluster saat ini {total_check}%. Wajib 100%!")
else:
    if st.sidebar.button("💾 SAVE CONFIGURATION", use_container_width=True):
        st.sidebar.success("Blueprint Locked!")

# 6. Komputasi Data Utama
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

        # 7. Render Dasbor Dasbor Utama
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
    st.info("Lengkapi nama saham di tiap kluster untuk memulai kalkulasi.")
