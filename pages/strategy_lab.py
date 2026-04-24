"""
Strateji Laboratuvarı
---------------------
50+ indikatör seçimi, kodsuz strateji oluşturma, backtest ve sonuç analizi.
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.data import get_stock_data, BIST100_TICKERS
from utils.indicators import (
    INDICATOR_CATALOG, INDICATORS_BY_KEY, INDICATORS_BY_CAT,
    compute_multiple, get_categories,
)
from utils.backtest import (
    run_backtest, signal_from_crossover, signal_from_threshold,
)
from utils.charts import candlestick_chart, equity_curve_chart, drawdown_chart, COLORS
import plotly.graph_objects as go

# ─── Hazır Strateji Şablonları ───
PRESET_STRATEGIES = {
    "📈 EMA Crossover (9/21)": {
        "desc":       "EMA(9) > EMA(21) → AL, EMA(9) < EMA(21) → SAT. Trend takip stratejisi.",
        "indicators": ["ema"],
        "params":     {"ema": {"length": 9}},
        "signal_type":"crossover",
        "fast":       "ema_9",
        "slow":       "ema_21",
        "extra_inds": [{"key":"ema","params":{"length":21}}],
    },
    "📉 RSI Oversold/Overbought": {
        "desc":       "RSI < 30 → AL, RSI > 70 → SAT. Mean-reversion stratejisi.",
        "indicators": ["rsi"],
        "params":     {},
        "signal_type":"threshold",
        "col":        "rsi_14",
        "buy_below":  30,
        "sell_above": 70,
    },
    "📊 MACD Signal Cross": {
        "desc":       "MACD histogram sıfır geçişi. Momentum stratejisi.",
        "indicators": ["macd"],
        "params":     {},
        "signal_type":"crossover",
        "fast":       "macd",
        "slow":       "macd_signal",
        "extra_inds": [],
    },
    "🔔 Bollinger Squeeze": {
        "desc":       "Fiyat alt banda değdiğinde AL, üst banda değdiğinde SAT.",
        "indicators": ["bbands"],
        "params":     {},
        "signal_type":"threshold",
        "col":        "bb_pct",
        "buy_below":  0.05,
        "sell_above": 0.95,
    },
    "⚡ SuperTrend": {
        "desc":       "SuperTrend yön değişiminde AL/SAT.",
        "indicators": ["supertrend"],
        "params":     {},
        "signal_type":"supertrend",
    },
}

def render():
    st.markdown("""
    <div style="margin-bottom:24px;">
        <h1 style="font-family:'Syne',sans-serif; font-size:1.8rem; font-weight:800;
                   color:#f1f5f9; margin:0;">🔬 Strateji Laboratuvarı</h1>
        <p style="font-family:'Space Mono',monospace; font-size:0.7rem; color:#475569; margin:4px 0 0 0;">
            50+ İndikatör · Kodsuz Strateji · Backtest Engine
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Ana Tab ──
    tab_builder, tab_backtest, tab_signals = st.tabs([
        "🏗️ Strateji Oluşturucu",
        "📈 Backtest Motoru",
        "📡 Sinyal Üretici",
    ])

    # ════════════════════════════════════════════
    # TAB 1: Strateji Oluşturucu
    # ════════════════════════════════════════════
    with tab_builder:
        c_left, c_right = st.columns([1, 2])

        with c_left:
            st.markdown("##### ⚙️ Hisse & Dönem")
            symbol = st.selectbox(
                "Hisse", list(BIST100_TICKERS.keys()),
                format_func=lambda x: f"{x} — {BIST100_TICKERS[x]}",
                key="lab_symbol",
            )
            period = st.selectbox("Veri Dönemi", ["1mo","3mo","6mo","1y","2y","5y"], index=3, key="lab_period")
            
            st.markdown("---")
            st.markdown("##### 🎯 Hazır Şablonlar")
            preset = st.selectbox("Şablon Seç", ["— Seç —"] + list(PRESET_STRATEGIES.keys()), key="lab_preset")
            if preset != "— Seç —":
                st.info(PRESET_STRATEGIES[preset]["desc"])

            st.markdown("---")
            st.markdown("##### 📦 İndikatör Seçimi")
            
            categories = get_categories()
            selected_indicators = {}
            custom_params       = {}

            for cat in categories:
                cat_inds = INDICATORS_BY_CAT[cat]
                with st.expander(f"**{cat}** ({len(cat_inds)} indikatör)", expanded=(cat=="Momentum")):
                    for ind in cat_inds:
                        cols = st.columns([3, 1])
                        with cols[0]:
                            checked = st.checkbox(
                                f"{ind.name}", key=f"ind_{ind.key}",
                                help=ind.description,
                            )
                        if checked:
                            selected_indicators[ind.key] = ind
                            # Parametre düzenleme
                            if ind.params:
                                with cols[1]:
                                    st.markdown(f"<span style='font-size:0.6rem;color:#64748b;'>params</span>",
                                                unsafe_allow_html=True)
                                param_str = st.text_input(
                                    f"Params ({ind.key})",
                                    value=str(ind.params),
                                    key=f"param_{ind.key}",
                                    label_visibility="collapsed",
                                )
                                try:
                                    custom_params[ind.key] = eval(param_str)
                                except Exception:
                                    custom_params[ind.key] = ind.params

            st.markdown("---")
            load_btn = st.button("🚀 Grafik Oluştur", use_container_width=True, type="primary", key="lab_load")

        # ── Sağ: Grafik ──
        with c_right:
            st.markdown("##### 📊 Grafik")
            
            # Preset seçildiyse otomatik indikatörleri ekle
            if preset != "— Seç —":
                strat = PRESET_STRATEGIES[preset]
                for key in strat["indicators"]:
                    selected_indicators[key] = INDICATORS_BY_KEY[key]
                for key, params in strat.get("params", {}).items():
                    custom_params[key] = params
                for extra in strat.get("extra_inds", []):
                    k = extra["key"]
                    selected_indicators[k] = INDICATORS_BY_KEY[k]
                    custom_params[k] = extra["params"]

            if load_btn or st.session_state.get("lab_auto_load", False):
                st.session_state["lab_auto_load"] = False
                keys = list(selected_indicators.keys())

                if not keys:
                    st.info("Sol panelden en az bir indikatör seçin.")
                else:
                    with st.spinner(f"{symbol} verisi çekiliyor + {len(keys)} indikatör hesaplanıyor..."):
                        df = get_stock_data(symbol, period=period)
                        
                        if df.empty:
                            st.error("Veri çekilemedi.")
                        else:
                            # Tüm indikatörleri hesapla
                            df = compute_multiple(df, keys, custom_params)
                            st.session_state["lab_df"]  = df
                            st.session_state["lab_keys"] = keys

            # Grafik göster
            if "lab_df" in st.session_state:
                df   = st.session_state["lab_df"]
                keys = st.session_state.get("lab_keys", [])
                
                # Grafik için overlay kolonları
                overlay_cols = []
                for key in keys:
                    for col in df.columns:
                        if col.startswith(key.replace("bbands","bb")):
                            overlay_cols.append(col)
                overlay_cols = list(set(overlay_cols))

                fig = candlestick_chart(df, title=f"{symbol} Strateji Grafiği", indicators=overlay_cols)
                st.plotly_chart(fig, use_container_width=True)

                # Son değerler tablosu
                st.markdown("##### 📋 Son İndikatör Değerleri")
                last_row = df.iloc[-1]
                ind_cols = [c for c in df.columns if c not in ["open","high","low","close","volume"]]
                if ind_cols:
                    vals = {col: round(float(last_row[col]), 4) if pd.notna(last_row[col]) else "N/A"
                            for col in ind_cols}
                    vals_df = pd.DataFrame(list(vals.items()), columns=["İndikatör", "Son Değer"])
                    st.dataframe(vals_df, use_container_width=True, hide_index=True, height=200)
            else:
                _placeholder_chart()

    # ════════════════════════════════════════════
    # TAB 2: Backtest Motoru
    # ════════════════════════════════════════════
    with tab_backtest:
        st.markdown("##### 🧪 Backtest Parametreleri")
        
        bt_cols = st.columns([1, 1, 1])
        with bt_cols[0]:
            bt_symbol = st.selectbox(
                "Hisse", list(BIST100_TICKERS.keys()),
                format_func=lambda x: f"{x} — {BIST100_TICKERS[x]}",
                key="bt_symbol",
            )
        with bt_cols[1]:
            bt_period = st.selectbox("Test Dönemi", ["1y","2y","5y","10y"], index=1, key="bt_period")
        with bt_cols[2]:
            bt_capital = st.number_input("Başlangıç Sermayesi (₺)", value=100_000,
                                         step=10_000, key="bt_capital")
        
        bt_cols2 = st.columns([1, 1, 1])
        with bt_cols2[0]:
            strategy_type = st.selectbox("Strateji Tipi",
                ["EMA Crossover", "RSI Threshold", "MACD Cross",
                 "Bollinger Bands", "SMA Crossover"],
                key="bt_strat_type")
        with bt_cols2[1]:
            stop_loss = st.slider("Stop Loss %", 0.0, 20.0, 5.0, 0.5, key="bt_sl")
            stop_loss = stop_loss / 100 if stop_loss > 0 else None
        with bt_cols2[2]:
            take_profit = st.slider("Take Profit %", 0.0, 50.0, 15.0, 1.0, key="bt_tp")
            take_profit = take_profit / 100 if take_profit > 0 else None

        st.markdown("---")

        if st.button("▶️ Backtest Çalıştır", use_container_width=True,
                     type="primary", key="bt_run"):
            with st.spinner(f"{bt_symbol} backtesting ({bt_period})..."):
                df = get_stock_data(bt_symbol, period=bt_period)
                
                if df.empty:
                    st.error("Veri çekilemedi.")
                else:
                    # Strateji seçimine göre indikatör & sinyal
                    if strategy_type == "EMA Crossover":
                        df = compute_multiple(df, ["ema"], {"ema": {"length": 9}})
                        df = compute_multiple(df, ["ema"], {"ema": {"length": 21}})
                        df["signal"] = signal_from_crossover(df, "ema_9", "ema_21")
                    
                    elif strategy_type == "SMA Crossover":
                        df = compute_multiple(df, ["sma"], {"sma": {"length": 20}})
                        df = compute_multiple(df, ["sma"], {"sma": {"length": 50}})
                        df["signal"] = signal_from_crossover(df, "sma_20", "sma_50")
                    
                    elif strategy_type == "RSI Threshold":
                        df = compute_multiple(df, ["rsi"], {})
                        df["signal"] = signal_from_threshold(
                            df, "rsi_14", buy_below=30, sell_above=70
                        )
                    
                    elif strategy_type == "MACD Cross":
                        df = compute_multiple(df, ["macd"], {})
                        df["signal"] = signal_from_crossover(df, "macd", "macd_signal")
                    
                    elif strategy_type == "Bollinger Bands":
                        df = compute_multiple(df, ["bbands"], {})
                        df["signal"] = signal_from_threshold(
                            df, "bb_pct", buy_below=0.05, sell_above=0.95
                        )
                    
                    result = run_backtest(
                        df, "signal",
                        initial_capital=bt_capital,
                        stop_loss_pct=stop_loss,
                        take_profit_pct=take_profit,
                    )
                    st.session_state["bt_result"] = result
                    st.session_state["bt_df"]     = df

        # ── Sonuçlar ──
        if "bt_result" in st.session_state:
            r  = st.session_state["bt_result"]
            df = st.session_state["bt_df"]

            st.markdown("---")
            st.markdown("#### 📊 Backtest Sonuçları")

            # Metrik kartları
            m1, m2, m3, m4 = st.columns(4)
            ret_color = "normal" if r.total_return_pct >= 0 else "inverse"
            m1.metric("💰 Toplam Getiri",   f"{r.total_return_pct:+.2f}%",  delta=f"B&H: {r.buy_hold_return:+.2f}%")
            m2.metric("📉 Max Drawdown",    f"{r.max_drawdown_pct:.2f}%")
            m3.metric("📐 Sharpe Ratio",    f"{r.sharpe_ratio:.2f}")
            m4.metric("🎯 Win Rate",         f"{r.win_rate_pct:.1f}%",      delta=f"{r.total_trades} işlem")

            m5, m6, m7, m8 = st.columns(4)
            m5.metric("📅 Yıllık Getiri",   f"{r.annual_return_pct:+.2f}%")
            m6.metric("✅ Kazanan İşlem",   f"{r.winning_trades}")
            m7.metric("❌ Kaybeden İşlem",  f"{r.losing_trades}")
            m8.metric("⚖️ Profit Factor",   f"{r.profit_factor:.2f}")

            # Grafikler
            gcol1, gcol2 = st.columns([2, 1])
            with gcol1:
                if not r.equity_curve.empty:
                    # Buy & hold equity
                    initial = float(r.equity_curve.iloc[0]) if len(r.equity_curve) > 0 else bt_capital
                    bh_curve = df["close"] / float(df["close"].iloc[0]) * bt_capital
                    bh_curve.name = "Buy & Hold"
                    
                    fig_eq = equity_curve_chart(
                        r.equity_curve, bh_curve,
                        title=f"{bt_symbol} · {strategy_type} Equity Eğrisi"
                    )
                    st.plotly_chart(fig_eq, use_container_width=True)
            
            with gcol2:
                if not r.equity_curve.empty:
                    fig_dd = drawdown_chart(r.equity_curve)
                    st.plotly_chart(fig_dd, use_container_width=True)

            # İşlem Listesi
            if not r.trades.empty:
                st.markdown("#### 📋 İşlem Geçmişi")
                display_trades = r.trades.copy()
                display_trades["pnl_pct"] = display_trades["pnl_pct"].apply(
                    lambda x: f"{'▲' if x>=0 else '▼'} {abs(x):.2f}%"
                )
                st.dataframe(display_trades, use_container_width=True, hide_index=True, height=250)

            st.markdown(f"""
            <div style="background:#111827; border:1px solid #1e2d4a; border-radius:8px;
                        padding:12px 16px; margin-top:16px; font-family:'Space Mono',monospace;
                        font-size:0.65rem; color:#475569;">
                ⚠️ Backtest geçmiş veriye dayanır. Gelecekteki getirileri garanti etmez.
                Test dönemi: {r.start_date} → {r.end_date}
            </div>
            """, unsafe_allow_html=True)

    # ════════════════════════════════════════════
    # TAB 3: Sinyal Üretici
    # ════════════════════════════════════════════
    with tab_signals:
        st.markdown("##### 📡 Anlık Sinyal Tarayıcı")
        st.markdown("Seçilen indikatör kriterlerine göre BIST hisselerini tarar.")

        sg_cols = st.columns([1, 1, 1, 1])
        with sg_cols[0]:
            sg_ind = st.selectbox("İndikatör",
                ["RSI(14) < 30 (Oversold)", "RSI(14) > 70 (Overbought)",
                 "Fiyat > EMA(20)", "Fiyat < EMA(20)",
                 "MACD > Signal", "Bollinger Alt Band"],
                key="sg_ind")
        with sg_cols[1]:
            sg_period = st.selectbox("Dönem", ["3mo","6mo","1y"], index=1, key="sg_period")
        with sg_cols[2]:
            max_stocks = st.slider("Max Hisse", 5, 30, 15, key="sg_max")
        with sg_cols[3]:
            st.markdown("<br>", unsafe_allow_html=True)
            scan_btn = st.button("🔍 Tara", use_container_width=True, type="primary", key="sg_scan")

        if scan_btn:
            symbols = list(BIST100_TICKERS.keys())[:max_stocks]
            results = []
            
            prog = st.progress(0, text="Hisseler taranıyor...")
            for i, sym in enumerate(symbols):
                prog.progress((i+1)/len(symbols), text=f"Taraniyor: {sym}")
                df = get_stock_data(sym, period=sg_period)
                if df.empty:
                    continue
                
                match = False
                val   = None
                
                if sg_ind == "RSI(14) < 30 (Oversold)":
                    df = compute_multiple(df, ["rsi"], {})
                    if "rsi_14" in df.columns:
                        val = round(float(df["rsi_14"].iloc[-1]), 2)
                        match = val < 30
                
                elif sg_ind == "RSI(14) > 70 (Overbought)":
                    df = compute_multiple(df, ["rsi"], {})
                    if "rsi_14" in df.columns:
                        val = round(float(df["rsi_14"].iloc[-1]), 2)
                        match = val > 70
                
                elif sg_ind == "Fiyat > EMA(20)":
                    df = compute_multiple(df, ["ema"], {"ema": {"length": 20}})
                    if "ema_20" in df.columns:
                        price = float(df["close"].iloc[-1])
                        ema   = float(df["ema_20"].iloc[-1])
                        val   = round(price / ema, 4)
                        match = price > ema
                
                elif sg_ind == "MACD > Signal":
                    df = compute_multiple(df, ["macd"], {})
                    if "macd" in df.columns:
                        val = round(float(df["macd"].iloc[-1]), 4)
                        match = float(df["macd"].iloc[-1]) > float(df["macd_signal"].iloc[-1])
                
                results.append({
                    "Sinyal": "✅" if match else "⬜",
                    "Sembol": sym,
                    "İsim":   BIST100_TICKERS.get(sym, ""),
                    "Fiyat":  round(float(df["close"].iloc[-1]), 2) if not df.empty else 0,
                    "Değer":  val,
                    "Kriter": sg_ind,
                })
            
            prog.empty()
            
            results_df = pd.DataFrame(results)
            matches    = results_df[results_df["Sinyal"] == "✅"]
            
            st.success(f"✅ {len(matches)} hisse '{sg_ind}' kriterini karşılıyor.")
            
            st.markdown("**Sinyal Veren Hisseler:**")
            if not matches.empty:
                st.dataframe(matches[["Sinyal","Sembol","İsim","Fiyat","Değer"]],
                             use_container_width=True, hide_index=True)
            else:
                st.info("Şu an bu kriteri karşılayan hisse bulunamadı.")
            
            with st.expander("Tüm Tarama Sonuçları"):
                st.dataframe(results_df, use_container_width=True, hide_index=True)

def _placeholder_chart():
    """Grafik yüklenmeden önce placeholder."""
    st.markdown("""
    <div style="background:#111827; border:2px dashed #1e2d4a; border-radius:12px;
                height:400px; display:flex; align-items:center; justify-content:center;
                flex-direction:column; gap:12px;">
        <div style="font-size:2rem;">📊</div>
        <div style="font-family:'Space Mono',monospace; font-size:0.75rem; color:#334155;
                    text-align:center;">
            Sol panelden indikatörleri seçin<br>ve "Grafik Oluştur" butonuna tıklayın.
        </div>
    </div>
    """, unsafe_allow_html=True)
