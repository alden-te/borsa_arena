"""
Sosyal Sinyal Ağı — Düzeltilmiş versiyon
"""
import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.data import BIST100, STOCK_NAMES, get_name

def _time_ago(dt: datetime) -> str:
    diff = (datetime.now() - dt).seconds
    if diff < 60:   return f"{diff}sn önce"
    if diff < 3600: return f"{diff//60}dk önce"
    return f"{diff//3600}sa önce"

def _demo_signals() -> list:
    random.seed(42)
    syms     = BIST100[:40]
    users    = ["QuantMaster","BorsaKralı","AlgoTrader","ValueInvestor","TechAnalyst","MomentumPro"]
    types    = ["AL","AL","AL","SAT","SAT","BEKLE"]
    reasons  = [
        "RSI(14)=27, güçlü oversold bölgesi.",
        "EMA(9) EMA(21) üzerine çıktı — golden cross.",
        "Bollinger alt bant teması, bounce beklenebilir.",
        "MACD negatif çaprazlama, momentum kaybı.",
        "ADX>35 + DI+ > DI−, güçlü yükseliş trendi.",
        "F/K 7.8 sektör ort. 12.4 — değerli.",
        "Hacim 20 günlük ort. 3.2x — breakout sinyali.",
        "Stochastic RSI aşırı satım bölgesinden çıkıyor.",
        "SuperTrend yön değiştirdi — AL sinyali.",
        "200 SMA destek noktası test ediliyor.",
    ]
    now = datetime.now()
    signals = []
    for i in range(30):
        stype = random.choice(types)
        ago   = now - timedelta(minutes=random.randint(3, 600))
        signals.append({
            "id":      i,
            "user":    random.choice(users),
            "symbol":  random.choice(syms),
            "type":    stype,
            "reason":  random.choice(reasons),
            "price":   round(random.uniform(5, 500), 2),
            "time":    ago,
            "likes":   random.randint(0, 55),
            "comments":random.randint(0, 15),
            "win_rate":random.randint(42, 84),
        })
    return sorted(signals, key=lambda x: x["time"], reverse=True)

def _signal_card(sig: dict):
    """Tek sinyal kartı — HTML olmadan, st.container ile."""
    type_colors = {"AL": "#00d4aa", "SAT": "#f87171", "BEKLE": "#f59e0b"}
    type_bgs    = {"AL": "#00d4aa18", "SAT": "#f8717118", "BEKLE": "#f59e0b18"}
    c  = type_colors.get(sig["type"], "#94a3b8")
    bg = type_bgs.get(sig["type"], "#11182718")

    with st.container():
        st.markdown(f"""
<div style="background:{bg};border:1px solid {c}40;border-left:3px solid {c};
    border-radius:8px;padding:12px 14px;margin-bottom:8px;">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">
        <div style="display:flex;align-items:center;gap:10px;">
            <span style="background:{c}22;border:1px solid {c};border-radius:5px;
                padding:3px 9px;font-family:'Space Mono',monospace;font-weight:700;
                font-size:.72rem;color:{c};">{sig["type"]}</span>
            <span style="font-family:'Space Mono',monospace;font-weight:700;
                color:#e2e8f0;font-size:.85rem;">{sig["symbol"]}</span>
            <span style="font-family:'Space Mono',monospace;font-size:.62rem;
                color:#475569;">— {get_name(sig["symbol"])}</span>
        </div>
        <div style="text-align:right;">
            <div style="font-family:'Space Mono',monospace;font-size:.6rem;color:#475569;">
                {_time_ago(sig["time"])}
            </div>
            <div style="font-family:'Space Mono',monospace;font-size:.6rem;color:{c};">
                Win: {sig["win_rate"]}%
            </div>
        </div>
    </div>
    <div style="font-family:'Space Mono',monospace;font-size:.7rem;color:#94a3b8;
        margin-bottom:8px;">
        {sig["reason"]}
    </div>
    <div style="display:flex;gap:14px;align-items:center;">
        <span style="font-family:'Syne',sans-serif;font-size:.72rem;font-weight:600;
            color:#334155;">👤 {sig["user"]}</span>
        <span style="font-family:'Space Mono',monospace;font-size:.62rem;color:#334155;">
            👍 {sig["likes"]} &nbsp;&nbsp; 💬 {sig["comments"]}
        </span>
    </div>
</div>""", unsafe_allow_html=True)

def render():
    st.markdown("""
    <div style="margin-bottom:20px;">
        <h1 style="font-family:'Syne',sans-serif;font-size:1.7rem;font-weight:800;
            color:#f1f5f9;margin:0;">📡 Sosyal Sinyal Ağı</h1>
        <p style="font-family:'Space Mono',monospace;font-size:.65rem;color:#475569;margin:4px 0 0 0;">
            Veri odaklı topluluk sinyalleri · Takip et · Sohbet odaları
        </p>
    </div>
    """, unsafe_allow_html=True)

    tab_feed, tab_share, tab_chat = st.tabs(["📡 Sinyal Akışı","📤 Sinyal Paylaş","💬 Sohbet Odaları"])
    signals = _demo_signals()

    # ══ SİNYAL AKIŞI ══
    with tab_feed:
        fc1, fc2, fc3, fc4 = st.columns([1,1,1,1])
        with fc1:
            f_type = st.selectbox("Sinyal", ["Tümü","AL","SAT","BEKLE"], key="sf_type")
        with fc2:
            f_sym  = st.selectbox("Hisse", ["Tümü"] + sorted(BIST100[:40]), key="sf_sym")
        with fc3:
            f_user = st.selectbox("Kullanıcı",
                ["Tümü","QuantMaster","BorsaKralı","AlgoTrader","ValueInvestor","TechAnalyst"],
                key="sf_user")
        with fc4:
            f_win  = st.slider("Min Win%", 0, 80, 0, key="sf_win")

        filtered = [
            s for s in signals
            if (f_type == "Tümü" or s["type"] == f_type)
            and (f_sym  == "Tümü" or s["symbol"] == f_sym)
            and (f_user == "Tümü" or s["user"] == f_user)
            and s["win_rate"] >= f_win
        ]

        al_cnt  = sum(1 for s in filtered if s["type"] == "AL")
        sat_cnt = sum(1 for s in filtered if s["type"] == "SAT")
        bk_cnt  = sum(1 for s in filtered if s["type"] == "BEKLE")

        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("Toplam Sinyal", len(filtered))
        sc2.metric("🟢 AL",  al_cnt)
        sc3.metric("🔴 SAT", sat_cnt)
        sc4.metric("🟡 BEKLE", bk_cnt)

        st.markdown("---")
        for sig in filtered[:20]:
            _signal_card(sig)

    # ══ SİNYAL PAYLAŞ ══
    with tab_share:
        user = st.session_state.get("user", {})
        st.markdown(f"##### Sinyal Paylaş — {user.get('name','')}")

        sc1, sc2 = st.columns(2)
        with sc1:
            sh_sym  = st.selectbox("Hisse", sorted(BIST100),
                                    format_func=lambda x: f"{x}  {get_name(x)}",
                                    key="sh_sym")
        with sc2:
            sh_type = st.selectbox("Sinyal", ["AL","SAT","BEKLE"], key="sh_type")

        sc3, sc4 = st.columns(2)
        with sc3:
            sh_price = st.number_input("Hedef Fiyat ₺ (opsiyonel)", min_value=0.0, value=0.0, step=0.5, key="sh_price")
        with sc4:
            sh_sl   = st.number_input("Stop Loss ₺ (opsiyonel)",   min_value=0.0, value=0.0, step=0.5, key="sh_sl")

        sh_inds = st.multiselect(
            "Dayandığı indikatörler",
            ["RSI","MACD","EMA","SMA","Bollinger","ADX","Stochastic","CCI","ATR","OBV","Fibonacci","SuperTrend","Ichimoku"],
            key="sh_inds"
        )
        sh_reason = st.text_area(
            "Teknik Gerekçe (min 20 karakter)",
            max_chars=500,
            placeholder="RSI(14) = 28, oversold bölgesinde. EMA9 > EMA21 yaklaşıyor...",
            key="sh_reason"
        )

        col_btn, col_hint = st.columns([1,2])
        with col_btn:
            pub_btn = st.button("📡 Yayınla", type="primary", use_container_width=True, key="sh_pub")
        with col_hint:
            st.markdown("""
            <div style="font-family:'Space Mono',monospace;font-size:.6rem;color:#475569;
                padding-top:6px;">
                💡 İndikatör ismi + sayısal değer içeren gerekçeler öne çıkar.
            </div>
            """, unsafe_allow_html=True)

        if pub_btn:
            if len(sh_reason) < 20:
                st.error("Gerekçe en az 20 karakter olmalıdır.")
            elif not sh_inds:
                st.warning("En az 1 indikatör seçin.")
            else:
                st.success(f"✅ **{sh_sym}** için **{sh_type}** sinyali yayınlandı! Takipçilerinize bildirim gönderildi.")

        # Kurallar
        with st.expander("📜 Sinyal Paylaşım Kuralları"):
            st.markdown("""
            **Zorunlu:**
            - Teknik veya temel analiz gerekçesi yazılmalıdır
            - En az 1 indikatör ismi belirtilmelidir

            **Yasak:**
            - "Yükselecek", "Düşecek" gibi gerekçesiz ifadeler
            - "Haber aldım", "İçeriden duydum" ifadeleri
            - Yanıltıcı sinyal paylaşımı hesap puanını düşürür

            Kurallara uymayan sinyaller moderatörler tarafından kaldırılır.
            """)

    # ══ SOHBET ODALARI ══
    with tab_chat:
        st.markdown("##### 💬 Hisse Sohbet Odaları")
        chat_sym = st.selectbox(
            "Oda Seç",
            sorted(BIST100[:40]),
            format_func=lambda x: f"#{x}  {get_name(x)}",
            key="chat_sym"
        )

        st.markdown(f"**#{chat_sym} — {get_name(chat_sym)} Sohbet Odası**")
        st.markdown("""
        <div style="background:#111827;border:1px solid #1e2d4a;border-radius:6px;
            padding:8px 12px;margin-bottom:10px;font-family:'Space Mono',monospace;
            font-size:.62rem;color:#334155;">
            ℹ️ Sadece veri odaklı mesajlar (indikatör/sayısal değer içeren) öne çıkar ve
            puanlanır. Sıradan yorumlar düşük görünürlük alır.
        </div>
        """, unsafe_allow_html=True)

        msgs = [
            {"user":"QuantMaster",   "msg":f"RSI(14)={random.randint(25,35):.0f} — güçlü oversold.", "time":"14:32","score":62},
            {"user":"AlgoTrader",    "msg":"EMA9 EMA21 üzerine geçiyor — golden cross yakın.",    "time":"14:28","score":45},
            {"user":"ValueInvestor", "msg":f"F/K={random.uniform(6,10):.1f}, sektör ort. 12.4.",  "time":"14:15","score":58},
            {"user":"TechAnalyst",   "msg":"Bollinger sıkışması devam ediyor, breakout yakın.",    "time":"13:58","score":33},
            {"user":"BorsaKralı",    "msg":"Hacim ortalamanın 2.7 katı — dikkat!",                 "time":"13:45","score":71},
        ]
        for msg in msgs:
            score_color = "#00d4aa" if msg["score"] >= 50 else "#475569"
            st.markdown(f"""
<div style="background:#111827;border:1px solid #1e2d4a;border-left:3px solid {score_color};
    border-radius:8px;padding:10px 14px;margin-bottom:6px;">
    <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
        <span style="font-family:'Space Mono',monospace;font-size:.7rem;
            color:#60a5fa;font-weight:700;">{msg["user"]}</span>
        <span style="font-family:'Space Mono',monospace;font-size:.6rem;color:{score_color};">
            ▲ {msg["score"]} · {msg["time"]}
        </span>
    </div>
    <div style="font-family:'Space Mono',monospace;font-size:.7rem;color:#94a3b8;">
        {msg["msg"]}
    </div>
</div>""", unsafe_allow_html=True)

        st.markdown("---")
        msg_in = st.text_input(
            "Mesajınız",
            placeholder="RSI(14)=32, EMA9 EMA21'e yaklaşıyor...",
            key="chat_in"
        )
        if st.button("💬 Gönder", key="chat_send"):
            keywords = ["rsi","macd","ema","sma","bollinger","adx","stoch","atr","obv","fk","pd","%","hacim"]
            if len(msg_in) < 10:
                st.warning("Mesaj en az 10 karakter olmalı.")
            elif not any(kw in msg_in.lower() for kw in keywords):
                st.warning("⚠️ Veri/indikatör içermeyen mesajlar düşük puan alır. Sayısal veri ekleyin.")
            else:
                st.success("✅ Mesajınız gönderildi! +5 puan kazandınız.")
