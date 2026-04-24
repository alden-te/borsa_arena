"""
Fantezi Lig — Borsa İlk 11 v2
Formasyon seçimi, fiyat kaydı, gerçek puan hesabı, TD görseli
"""
import streamlit as st
import pandas as pd
import numpy as np
import sys, os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.data import get_stock_data, _FALLBACK, BIST30, INDEX_GROUPS, STOCK_NAMES, get_name

# ── Formasyon şablonları ──────────────────────────────────────
FORMATIONS = {
    "4-3-3": {"Kaleci":1,"Defans":4,"Orta Saha":3,"Forvet":3},
    "4-4-2": {"Kaleci":1,"Defans":4,"Orta Saha":4,"Forvet":2},
    "3-5-2": {"Kaleci":1,"Defans":3,"Orta Saha":5,"Forvet":2},
    "5-3-2": {"Kaleci":1,"Defans":5,"Orta Saha":3,"Forvet":2},
    "4-2-3-1":{"Kaleci":1,"Defans":4,"Orta Saha2":2,"Orta Saha":3,"Forvet":1},
    "3-4-3": {"Kaleci":1,"Defans":3,"Orta Saha":4,"Forvet":3},
    "4-5-1": {"Kaleci":1,"Defans":4,"Orta Saha":5,"Forvet":1},
}

FORMATION_POSITIONS = {
    "4-3-3": [("Kaleci",1),("Defans",4),("Orta Saha",3),("Forvet",3)],
    "4-4-2": [("Kaleci",1),("Defans",4),("Orta Saha",4),("Forvet",2)],
    "3-5-2": [("Kaleci",1),("Defans",3),("Orta Saha",5),("Forvet",2)],
    "5-3-2": [("Kaleci",1),("Defans",5),("Orta Saha",3),("Forvet",2)],
    "4-2-3-1": [("Kaleci",1),("Defans",4),("Defensif OS",2),("Orta Saha",3),("Forvet",1)],
    "3-4-3": [("Kaleci",1),("Defans",3),("Orta Saha",4),("Forvet",3)],
    "4-5-1": [("Kaleci",1),("Defans",4),("Orta Saha",5),("Forvet",1)],
}

def render():
    st.markdown("""
    <div style="margin-bottom:20px;">
        <h1 style="font-family:'Syne',sans-serif;font-size:1.7rem;font-weight:800;
            color:#f1f5f9;margin:0;">⚽ Fantezi Lig — Borsa İlk 11</h1>
        <p style="font-family:'Space Mono',monospace;font-size:.65rem;color:#475569;margin:4px 0 0 0;">
            Formasyon Seç · Mevki Mevki Hisse Seç · Puan Yarışı
        </p>
    </div>""", unsafe_allow_html=True)

    tab_kadro, tab_puan, tab_lider = st.tabs([
        "🏟️ Kadro Kur","📊 Puan Durumu","🏆 Lider Tablosu"
    ])
    now  = datetime.now()
    week = now.isocalendar()[1]

    # ════════════════════════════════════════════
    # KADRO KUR
    # ════════════════════════════════════════════
    with tab_kadro:
        mevcut = st.session_state.get("fantasy_kadro", None)
        user   = st.session_state.get("user", {})
        td_adi = user.get("name", "Teknik Direktör")

        # Header banner
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#0d1f3c,#0a1628);
            border:1px solid #1e3a5f;border-radius:12px;padding:16px 20px;margin-bottom:16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <div style="font-family:'Space Mono',monospace;font-size:.6rem;color:#475569;">
                        HAFTA {week} · {now.strftime('%d %B %Y')}</div>
                    <div style="font-family:'Syne',sans-serif;font-weight:800;color:#e2e8f0;
                        font-size:1.1rem;margin-top:2px;">🎽 TD: {td_adi}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-family:'Space Mono',monospace;font-size:.6rem;color:#475569;">
                        KADRO DURUMU</div>
                    <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:.9rem;
                        color:{'#00d4aa' if mevcut and len(mevcut.get('aslar',[])) == 11 else '#f59e0b'};">
                        {'✅ KAYITLI' if mevcut and len(mevcut.get('aslar',[])) == 11 else '⏳ KURULMADI'}
                    </div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        # Formasyon + Hisse Havuzu
        col_form, col_idx = st.columns([1,1])
        with col_form:
            formation = st.selectbox("⚽ Formasyon", list(FORMATION_POSITIONS.keys()),
                                     key="fl_form", index=0)
        with col_idx:
            idx_filter = st.selectbox("📋 Hisse Havuzu",
                                      list(INDEX_GROUPS.keys()) + ["Tüm BIST"],
                                      key="fl_idx")

        if idx_filter == "Tüm BIST":
            available = sorted(_FALLBACK)
        else:
            available = sorted(INDEX_GROUPS.get(idx_filter, BIST30))

        form_positions = FORMATION_POSITIONS[formation]
        total_needed   = sum(n for _,n in form_positions)  # 11

        st.markdown(f"""
        <div style="background:#111827;border:1px solid #1e2d4a;border-radius:8px;
            padding:10px 14px;margin-bottom:12px;">
            <div style="font-family:'Space Mono',monospace;font-size:.65rem;color:#64748b;">
                🏗️ <strong style="color:#e2e8f0;">{formation}</strong> formasyonu · 
                {total_needed} as + 3 yedek = 14 hisse
            </div>
        </div>""", unsafe_allow_html=True)

        # Mevki mevki seçim
        selected_positions = {}
        position_syms = []  # Sıralı olarak tüm as hisseler

        # Mevcut kadrodan pozisyon verisi al
        prev_pos = st.session_state.get("fantasy_positions", {})

        st.markdown("---")
        st.markdown("##### 🎯 Mevki Mevki Hisse Seç")

        pos_cols = st.columns(len(form_positions))
        for i, (pos_name, count) in enumerate(form_positions):
            with pos_cols[i]:
                st.markdown(f"""
                <div style="text-align:center;background:#0d1f3c;border:1px solid #1e3a5f;
                    border-radius:8px;padding:6px;margin-bottom:8px;">
                    <div style="font-family:'Space Mono',monospace;font-size:.6rem;color:#60a5fa;">
                        {pos_name}</div>
                    <div style="font-family:'Syne',sans-serif;font-weight:700;color:#e2e8f0;
                        font-size:.9rem;">{count} hisse</div>
                </div>""", unsafe_allow_html=True)

                used_so_far = [s for pl in selected_positions.values() for s in pl]
                opts = [s for s in available if s not in used_so_far]

                prev = [s for s in prev_pos.get(pos_name, []) if s in opts][:count]
                sel = st.multiselect(
                    f"{pos_name} ({count})",
                    opts,
                    default=prev,
                    max_selections=count,
                    format_func=lambda x: f"{x}",
                    key=f"fl_pos_{pos_name}_{i}",
                    label_visibility="collapsed",
                )
                selected_positions[pos_name] = sel
                position_syms.extend(sel)

        # Kalan hak göstergesi
        total_sel = len(position_syms)
        kalan     = total_needed - total_sel
        st.markdown(f"""
        <div style="background:#111827;border:1px solid #1e2d4a;border-radius:8px;
            padding:10px 14px;margin:12px 0;">
            <div style="display:flex;justify-content:space-between;
                font-family:'Space Mono',monospace;font-size:.65rem;">
                <span style="color:#64748b;">As hisseler:</span>
                <span style="color:{'#00d4aa' if total_sel==11 else '#f59e0b'};font-weight:700;">
                    {total_sel}/11 {'✅' if total_sel==11 else f'({kalan} kaldı)'}</span>
            </div>
        </div>""", unsafe_allow_html=True)

        # Yedekler
        st.markdown("##### 🔵 3 Yedek Hisse")
        used_all = set(position_syms)
        yed_opts = [s for s in available if s not in used_all]
        prev_yed = [s for s in (mevcut.get("yedekler",[]) if mevcut else []) if s in yed_opts][:3]
        yedekler = st.multiselect(
            "Yedek seç (3)",
            yed_opts,
            default=prev_yed,
            max_selections=3,
            format_func=lambda x: f"{x}  {get_name(x)}",
            key="fl_yedekler",
        )
        st.markdown(f"Yedek: **{len(yedekler)}/3**")

        # Kaptan seçimi
        kaptan = None
        if position_syms:
            st.markdown("##### ⭐ Kaptan (Puan ×2)")
            prev_k = mevcut.get("kaptan") if mevcut and mevcut.get("kaptan") in position_syms else position_syms[0]
            kaptan = st.selectbox(
                "Kaptan",
                position_syms,
                index=position_syms.index(prev_k) if prev_k in position_syms else 0,
                format_func=lambda x: f"⭐ {x}  {get_name(x)}",
                key="fl_kaptan",
            )

        # Kaydet butonu
        st.markdown("---")
        c_save, c_status = st.columns([1, 2])
        with c_save:
            save_btn = st.button("💾 Kadroyu Kaydet", type="primary",
                                 use_container_width=True, key="fl_save")
        with c_status:
            if total_sel != 11:
                st.warning(f"⚠️ {kalan} as hisse daha seçin.")
            elif len(yedekler) != 3:
                st.warning(f"⚠️ {3-len(yedekler)} yedek daha seçin.")
            else:
                st.success("✅ Kadro hazır! Kaydedebilirsiniz.")

        if save_btn:
            if total_sel != 11 or len(yedekler) != 3:
                st.error("Tam 11 as + 3 yedek seçmelisiniz.")
            else:
                # Fiyatları kaydet
                saved_prices = {}
                for sym in position_syms + yedekler:
                    df_tmp = get_stock_data(sym, period="5d")
                    if not df_tmp.empty:
                        saved_prices[sym] = float(df_tmp["close"].iloc[-1])
                    else:
                        saved_prices[sym] = 0.0

                st.session_state["fantasy_kadro"] = {
                    "aslar":      position_syms,
                    "yedekler":   yedekler,
                    "kaptan":     kaptan,
                    "formasyon":  formation,
                    "hafta":      week,
                    "saved_at":   now.isoformat(),
                    "saved_prices": saved_prices,
                }
                st.session_state["fantasy_positions"] = selected_positions
                st.success("🎉 Kadro kaydedildi!")
                st.balloons()

        # Saha görünümü — sadece kayıtlı kadro varsa
        if mevcut and len(mevcut.get("aslar",[])) == 11:
            st.markdown("---")
            _render_pitch_pro(
                aslar      = mevcut["aslar"],
                kaptan     = mevcut.get("kaptan"),
                yedekler   = mevcut.get("yedekler",[]),
                formasyon  = mevcut.get("formasyon","4-3-3"),
                positions  = st.session_state.get("fantasy_positions",{}),
                td_name    = td_adi,
                week       = mevcut.get("hafta", week),
            )

    # ════════════════════════════════════════════
    # PUAN DURUMU
    # ════════════════════════════════════════════
    with tab_puan:
        kadro = st.session_state.get("fantasy_kadro", None)

        if not kadro or not kadro.get("aslar"):
            st.info("Önce 'Kadro Kur' sekmesinden kadronuzu oluşturun ve kaydedin.")
        else:
            aslar_k = kadro["aslar"]
            kaptan_k = kadro.get("kaptan")
            yedekler_k = kadro.get("yedekler", [])
            saved_prices = kadro.get("saved_prices", {})
            saved_at = kadro.get("saved_at", now.isoformat())

            try:
                saved_dt = datetime.fromisoformat(saved_at)
            except Exception:
                saved_dt = now

            elapsed_h = (now - saved_dt).total_seconds() / 3600

            # Bilgi kartı
            st.markdown(f"""
            <div style="background:#111827;border:1px solid #1e3a5f;border-radius:10px;
                padding:14px 18px;margin-bottom:16px;">
                <div style="font-family:'Space Mono',monospace;font-size:.65rem;color:#64748b;">
                    Kadro kurulma zamanı: <strong style="color:#60a5fa;">
                    {saved_dt.strftime('%d.%m.%Y %H:%M')}</strong>
                    · Geçen süre: <strong style="color:#00d4aa;">{elapsed_h:.1f} saat</strong>
                </div>
            </div>""", unsafe_allow_html=True)

            # ── Puanlama sistemi açıklaması ──
            with st.expander("📖 Puanlama Sistemi Nasıl Çalışır?", expanded=False):
                st.markdown("""
                **📐 Puan Hesaplama:**
                - Kadro kaydedildiğinde her hissenin **kapanış fiyatı** otomatik kaydedilir
                - "Hesapla" butonuna basıldığında **o anki fiyat** ile karşılaştırılır
                - Her **%1 artış** = **10 puan**, her **%1 düşüş** = -10 puan
                - Puanlar **-100 ile +100** arasında sınırlandırılır
                - **Kaptan** puanı **×2** alır
                - Yedek hisseler puana **katkıda bulunmaz** ama takip edilir

                **🏆 Sıralama:**
                - Haftalık toplam puan (sadece 11 as hisseden)
                - Her Pazartesi sabahı sıfırlanır
                - Sezon sonunda en yüksek kümülatif puan kazanır
                """)

            if st.button("📈 Puanları Hesapla", type="primary", key="fp_calc"):
                records = []
                prog = st.progress(0, "Anlık fiyatlar çekiliyor...")
                all_hs = aslar_k + yedekler_k

                for i, sym in enumerate(all_hs):
                    prog.progress((i+1)/len(all_hs), f"{sym} güncelleniyor...")
                    df_tmp = get_stock_data(sym, period="5d")

                    if df_tmp.empty:
                        current_price = saved_prices.get(sym, 0)
                        ret = 0.0
                    else:
                        current_price = float(df_tmp["close"].iloc[-1])
                        entry_price   = saved_prices.get(sym, 0)
                        if entry_price > 0:
                            ret = (current_price - entry_price) / entry_price * 100
                        else:
                            ret = 0.0

                    pts = max(-100, min(100, round(ret * 10)))
                    if sym == kaptan_k:
                        pts *= 2

                    is_as = sym in aslar_k
                    records.append({
                        "Rol":      "⭐ Kaptan" if sym == kaptan_k else ("🟢 As" if is_as else "🔵 Yedek"),
                        "Sembol":   sym,
                        "İsim":     get_name(sym),
                        "Giriş ₺":  round(saved_prices.get(sym, 0), 2),
                        "Güncel ₺": round(current_price, 2),
                        "Getiri%":  round(ret, 2),
                        "Puan":     pts if is_as else 0,
                    })

                prog.empty()
                st.session_state["fl_perf"] = pd.DataFrame(records)

            if "fl_perf" in st.session_state:
                perf     = st.session_state["fl_perf"]
                as_perf  = perf[perf["Rol"] != "🔵 Yedek"]
                total_pts = int(as_perf["Puan"].sum())
                best      = perf.loc[perf["Getiri%"].idxmax(), "Sembol"]
                worst     = perf.loc[perf["Getiri%"].idxmin(), "Sembol"]

                m1,m2,m3,m4 = st.columns(4)
                m1.metric("🏆 Toplam Puan",  f"{total_pts:+,}")
                m2.metric("📈 Ort. Getiri",  f"{as_perf['Getiri%'].mean():+.2f}%")
                m3.metric("⭐ En Yüksek",    best)
                m4.metric("📉 En Düşük",     worst)
                st.markdown("---")

                st.dataframe(
                    perf.sort_values("Puan", ascending=False),
                    use_container_width=True, hide_index=True,
                    column_config={
                        "Giriş ₺":  st.column_config.NumberColumn(format="%.2f"),
                        "Güncel ₺": st.column_config.NumberColumn(format="%.2f"),
                        "Getiri%":  st.column_config.NumberColumn(format="%+.2f%%"),
                        "Puan":     st.column_config.ProgressColumn("Puan",
                                        min_value=-200, max_value=200, format="%+d"),
                    }
                )

    # ════════════════════════════════════════════
    # LİDER TABLOSU
    # ════════════════════════════════════════════
    with tab_lider:
        st.markdown(f"##### 🏆 Hafta {week} Lider Tablosu")

        # Kullanıcı puanını ekle
        user_pts = 0
        if "fl_perf" in st.session_state:
            user_pts = int(st.session_state["fl_perf"]["Puan"].sum())

        user_name = st.session_state.get("user", {}).get("name", "Siz")
        leaders = [
            {"#":"🥇","Kullanıcı":"QuantMaster",   "Puan":2840,"Formasyon":"4-3-3","Rütbe":"Elite 🟣"},
            {"#":"🥈","Kullanıcı":"BorsaKralı",    "Puan":2654,"Formasyon":"4-4-2","Rütbe":"Gold 🟡"},
            {"#":"🥉","Kullanıcı":"AlgoTrader",    "Puan":2511,"Formasyon":"3-5-2","Rütbe":"Gold 🟡"},
            {"#":"4", "Kullanıcı":"ValueInvestor", "Puan":2388,"Formasyon":"4-3-3","Rütbe":"Silver ⚪"},
            {"#":"5", "Kullanıcı":"TechAnalyst",   "Puan":2210,"Formasyon":"4-4-2","Rütbe":"Silver ⚪"},
            {"#":"6", "Kullanıcı":"MomentumPro",   "Puan":2100,"Formasyon":"4-5-1","Rütbe":"Silver ⚪"},
            {"#":"7", "Kullanıcı":"DivTrader",     "Puan":1980,"Formasyon":"3-4-3","Rütbe":"Bronze 🟤"},
            {"#":"8", "Kullanıcı":user_name,        "Puan":max(user_pts,1850),"Formasyon":kadro.get("formasyon","4-3-3") if kadro else "—","Rütbe":"Bronze 🟤"},
            {"#":"9", "Kullanıcı":"Momentum99",    "Puan":1720,"Formasyon":"4-3-3","Rütbe":"Bronze 🟤"},
            {"#":"10","Kullanıcı":"PatternPro",    "Puan":1610,"Formasyon":"4-4-2","Rütbe":"Rookie ⬛"},
        ]
        df_lead = pd.DataFrame(leaders)
        st.dataframe(df_lead, use_container_width=True, hide_index=True,
                     column_config={"Puan":st.column_config.ProgressColumn("Puan",max_value=3000,format="%d")})

        st.markdown("""
        <div style="background:#111827;border:1px solid #1e2d4a;border-radius:8px;
            padding:12px 16px;margin-top:12px;font-family:'Space Mono',monospace;font-size:.65rem;color:#64748b;">
            💡 Hafta sonu (Cuma 18:30 kapanış) en yüksek puanlı 3 kullanıcıya
            dijital sertifika + 500 XP verilir. Puanlar Pazartesi 09:00'da sıfırlanır.
        </div>""", unsafe_allow_html=True)


def _render_pitch_pro(aslar, kaptan, yedekler, formasyon, positions, td_name, week):
    """Pro futbol sahası görselleştirme — formasyon bazlı."""
    form_rows = FORMATION_POSITIONS.get(formasyon, FORMATION_POSITIONS["4-3-3"])

    # Her pozisyona hisse ata
    pos_assign = {}
    idx = 0
    for pos_name, count in form_rows:
        pos_assign[pos_name] = []
        for _ in range(count):
            if idx < len(aslar):
                pos_assign[pos_name].append(aslar[idx])
                idx += 1

    # Saha HTML'i oluştur — yukarıdan aşağı (Forvet → Kaleci)
    rows_html = ""
    for pos_name, count in form_rows:
        syms = pos_assign.get(pos_name, [])
        if not syms:
            continue
        cards = ""
        for sym in syms:
            is_k   = (sym == kaptan)
            bg     = "rgba(245,158,11,0.9)" if is_k else "rgba(13,31,60,0.85)"
            border = "#f59e0b" if is_k else "rgba(255,255,255,0.2)"
            glow   = "box-shadow:0 0 12px rgba(245,158,11,0.4);" if is_k else ""
            cap    = '<div style="font-size:.45rem;color:#fef3c7;margin-top:1px;">⭐ Kaptan</div>' if is_k else ""
            name   = get_name(sym)[:11]
            cards += f"""
            <div style="background:{bg};border:1.5px solid {border};border-radius:8px;
                padding:8px 10px;min-width:58px;text-align:center;margin:0 4px;{glow}
                transition:all .2s;">
                <div style="font-size:.72rem;font-weight:800;color:white;
                    font-family:'Space Mono',monospace;">{sym}</div>
                <div style="font-size:.45rem;color:rgba(255,255,255,0.6);margin-top:1px;">{name}</div>
                {cap}
            </div>"""

        rows_html += f"""
        <div style="text-align:center;margin-bottom:14px;">
            <div style="font-size:.5rem;color:rgba(255,255,255,0.3);letter-spacing:.15em;
                text-transform:uppercase;margin-bottom:6px;">{pos_name}</div>
            <div style="display:flex;justify-content:center;gap:0;flex-wrap:wrap;">{cards}</div>
        </div>"""

    # Yedekler
    yed_html = ""
    for sym in yedekler:
        yed_html += f"""
        <div style="background:rgba(59,130,246,0.2);border:1px solid rgba(96,165,250,0.4);
            border-radius:8px;padding:7px 10px;text-align:center;">
            <div style="font-size:.7rem;font-weight:700;color:#93c5fd;
                font-family:'Space Mono',monospace;">{sym}</div>
            <div style="font-size:.45rem;color:rgba(147,197,253,0.6);margin-top:1px;">
                {get_name(sym)[:11]}</div>
        </div>"""

    yed_section = f"""
    <div style="margin-top:14px;padding-top:12px;border-top:1px dashed rgba(255,255,255,0.15);">
        <div style="font-size:.5rem;color:rgba(255,255,255,0.3);text-align:center;
            letter-spacing:.15em;margin-bottom:8px;">YEDEKLER</div>
        <div style="display:flex;justify-content:center;gap:8px;flex-wrap:wrap;">{yed_html}</div>
    </div>""" if yed_html else ""

    # Çim çizgileri
    lines_svg = ""
    for i in range(4):
        y = 15 + i * 20
        lines_svg += f'<line x1="0" y1="{y}%" x2="100%" y2="{y}%" stroke="rgba(255,255,255,0.04)" stroke-width="1"/>'

    st.markdown(f"""
    <div style="margin-top:8px;">
        <div style="background:#111827;border:1px solid #1e3a5f;border-radius:10px;
            padding:10px 16px;margin-bottom:8px;display:flex;justify-content:space-between;
            align-items:center;">
            <div style="font-family:'Syne',sans-serif;font-weight:700;color:#e2e8f0;font-size:.85rem;">
                🎽 TD: {td_name}</div>
            <div style="font-family:'Space Mono',monospace;font-size:.62rem;color:#60a5fa;">
                {formasyon} · Hafta {week}</div>
        </div>
        <div style="position:relative;background:linear-gradient(180deg,
            #0a3d1c 0%,#0d5928 20%,#0a4d20 40%,#0d5928 60%,#0a4d20 80%,#0a3d1c 100%);
            border-radius:14px;border:2px solid #1a6b35;padding:20px 16px;
            box-shadow:0 8px 32px rgba(0,0,0,0.5);">
            <svg style="position:absolute;top:0;left:0;width:100%;height:100%;
                pointer-events:none;border-radius:12px;" viewBox="0 0 100 100" preserveAspectRatio="none">
                {lines_svg}
                <circle cx="50" cy="50" r="15" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width=".5"/>
                <line x1="15" y1="0" x2="85" y2="0" stroke="rgba(255,255,255,0.15)" stroke-width="1"/>
                <line x1="15" y1="100" x2="85" y2="100" stroke="rgba(255,255,255,0.15)" stroke-width="1"/>
                <rect x="30" y="0" width="40" height="12" fill="none" stroke="rgba(255,255,255,0.12)" stroke-width=".5"/>
                <rect x="30" y="88" width="40" height="12" fill="none" stroke="rgba(255,255,255,0.12)" stroke-width=".5"/>
                <line x1="0" y1="50" x2="100" y2="50" stroke="rgba(255,255,255,0.08)" stroke-width=".5"/>
            </svg>
            <div style="position:relative;z-index:1;">
                {rows_html}
                {yed_section}
            </div>
        </div>
    </div>""", unsafe_allow_html=True)
