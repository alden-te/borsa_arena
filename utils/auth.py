"""
Auth Modülü — Session persistence + Supabase opsiyonel
"""
import streamlit as st
import hashlib
import json
import os
from datetime import datetime
from typing import Optional

# Demo kullanıcılar
DEMO_USERS = {
    "demo@borsaarena.com": {"password_hash": hashlib.sha256(b"demo123").hexdigest(),
                            "name": "Demo Yatırımcı", "xp": 1250},
    "admin@borsaarena.com": {"password_hash": hashlib.sha256(b"admin123").hexdigest(),
                             "name": "Arena Admin", "xp": 9999},
}
_SESSION_USERS: dict = {}   # Runtime'da kayıt olanlar

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def rank_from_xp(xp: int) -> tuple:
    if xp < 500:  return "Rookie",  "#94a3b8"
    if xp < 1500: return "Silver",  "#cbd5e1"
    if xp < 3000: return "Gold",    "#f59e0b"
    if xp < 6000: return "Plat",    "#60a5fa"
    return "Elite", "#00d4aa"

def _supabase():
    try:
        url = st.secrets.get("SUPABASE_URL","")
        key = st.secrets.get("SUPABASE_KEY","")
        if url and key and url.startswith("https://"):
            from supabase import create_client
            return create_client(url, key)
    except Exception:
        pass
    return None

def login_user(email: str, password: str) -> Optional[dict]:
    sb = _supabase()
    if sb:
        try:
            res = sb.auth.sign_in_with_password({"email": email, "password": password})
            if res.user:
                return {"email": email, "name": email.split("@")[0].title(), "xp": 0}
        except Exception:
            pass
    all_u = {**DEMO_USERS, **_SESSION_USERS}
    u = all_u.get(email.lower())
    if u and u["password_hash"] == hash_pw(password):
        return {"email": email, "name": u["name"], "xp": u.get("xp", 0)}
    return None

def register_user(email: str, password: str, name: str) -> tuple:
    sb = _supabase()
    if sb:
        try:
            res = sb.auth.sign_up({"email": email, "password": password})
            if res.user:
                return True, "Hesabınız oluşturuldu!"
        except Exception as e:
            return False, f"Kayıt hatası: {e}"
    all_u = {**DEMO_USERS, **_SESSION_USERS}
    if email.lower() in all_u:
        return False, "Bu e-posta zaten kayıtlı."
    if len(password) < 8:
        return False, "Şifre en az 8 karakter olmalı."
    _SESSION_USERS[email.lower()] = {
        "password_hash": hash_pw(password),
        "name": name, "xp": 0,
        "joined": datetime.now().strftime("%Y-%m-%d"),
    }
    return True, "Hesap oluşturuldu! Giriş yapabilirsiniz."

# ──────────────────────────────────────────────────────────────
# "Beni Hatırla" — st.query_params tabanlı basit token
# ──────────────────────────────────────────────────────────────
_REMEMBER_KEY = "ba_remember"

def _save_remember(email: str, name: str, xp: int):
    """URL query param olarak token sakla — production'da cookie/localStorage kullanılır."""
    token = hashlib.sha256(f"{email}:borsa_arena_salt_2024".encode()).hexdigest()[:16]
    try:
        st.query_params["token"] = token
        # Session state'e de kaydet (sayfa yenilenmesine dayanıklı)
        st.session_state["_remember_email"] = email
        st.session_state["_remember_name"]  = name
        st.session_state["_remember_xp"]    = xp
        st.session_state["_remember_token"] = token
    except Exception:
        pass

def _load_remember() -> Optional[dict]:
    """Kaydedilmiş oturumu yükle."""
    try:
        email = st.session_state.get("_remember_email","")
        token = st.session_state.get("_remember_token","")
        name  = st.session_state.get("_remember_name","")
        xp    = st.session_state.get("_remember_xp", 0)
        if email and token:
            expected = hashlib.sha256(f"{email}:borsa_arena_salt_2024".encode()).hexdigest()[:16]
            if token == expected:
                return {"email": email, "name": name, "xp": xp}
    except Exception:
        pass
    return None

def _clear_remember():
    for k in ["_remember_email","_remember_name","_remember_xp","_remember_token"]:
        st.session_state.pop(k, None)
    try:
        st.query_params.clear()
    except Exception:
        pass

# ── Giriş Sayfası ────────────────────────────────────────────
def login_page():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@800&family=Space+Mono&display=swap');
    .stApp{background:#0a0e1a;}
    [data-testid="stSidebarNav"]{display:none!important;}
    </style>""", unsafe_allow_html=True)

    # Beni hatırla kontrolü
    remembered = _load_remember()
    if remembered:
        st.session_state.authenticated = True
        st.session_state.user = remembered
        st.rerun()
        return

    _, center, _ = st.columns([1, 1.1, 1])
    with center:
        st.markdown("""
        <div style="text-align:center;padding:40px 0 28px 0;">
            <div style="font-family:'Syne',sans-serif;font-size:2.8rem;font-weight:800;
                background:linear-gradient(135deg,#00d4aa 0%,#0066ff 100%);
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                background-clip:text;line-height:1.1;">📊<br>BORSA ARENA</div>
            <div style="font-family:'Space Mono',monospace;font-size:.65rem;
                color:#334155;letter-spacing:.2em;margin-top:8px;">QUANT & SOCIAL HUB v0.5</div>
        </div>""", unsafe_allow_html=True)

        tab_in, tab_reg = st.tabs(["🔑 Giriş Yap","✨ Kayıt Ol"])

        with tab_in:
            st.markdown("<br>", unsafe_allow_html=True)
            email    = st.text_input("E-posta", placeholder="investor@mail.com", key="li_email")
            pw       = st.text_input("Şifre", type="password", placeholder="••••••••", key="li_pw")
            remember = st.checkbox("🔒 Beni hatırla (bu cihazda)", value=True, key="li_remember")
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("🚀 Giriş Yap", use_container_width=True, type="primary", key="li_btn"):
                if email and pw:
                    u = login_user(email.strip(), pw)
                    if u:
                        st.session_state.authenticated = True
                        st.session_state.user = u
                        if remember:
                            _save_remember(u["email"], u["name"], u.get("xp",0))
                        st.rerun()
                    else:
                        st.error("❌ E-posta veya şifre hatalı.")
                else:
                    st.warning("Tüm alanları doldurun.")

            st.markdown("""
            <div style="background:#111827;border:1px solid #1e2d4a;border-radius:8px;
                padding:10px 14px;margin-top:16px;font-family:'Space Mono',monospace;font-size:.62rem;color:#475569;">
                🎯 Demo: <span style="color:#60a5fa;">demo@borsaarena.com</span> / demo123<br>
                💡 Gerçek hesap için kayıt ol. Tüm özellikler ücretsiz.
            </div>""", unsafe_allow_html=True)

        with tab_reg:
            st.markdown("<br>", unsafe_allow_html=True)
            rn  = st.text_input("Ad Soyad",    placeholder="Ahmet Yılmaz",        key="rg_name")
            re  = st.text_input("E-posta",     placeholder="investor@mail.com",   key="rg_email")
            rp  = st.text_input("Şifre",       type="password", placeholder="En az 8 karakter", key="rg_pw")
            rp2 = st.text_input("Şifre Tekrar",type="password", placeholder="••••••••", key="rg_pw2")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✨ Hesap Oluştur", use_container_width=True, type="primary", key="rg_btn"):
                if not all([rn,re,rp,rp2]):
                    st.warning("Tüm alanları doldurun.")
                elif rp != rp2:
                    st.error("Şifreler eşleşmiyor.")
                else:
                    ok, msg = register_user(re.strip(), rp, rn.strip())
                    if ok:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(msg)

        st.markdown("""
        <div style="font-family:'Space Mono',monospace;font-size:.55rem;
            color:#1e293b;text-align:center;margin-top:28px;line-height:1.8;">
            ⚠️ Yatırım tavsiyesi değildir · v0.5 · MIT
        </div>""", unsafe_allow_html=True)


def sidebar_user_menu():
    u = st.session_state.get("user", {})
    if not u: return
    xp = u.get("xp",0)
    rank, rc = rank_from_xp(xp)
    st.markdown(f"""
    <div style="background:#111827;border:1px solid #1e2d4a;border-radius:8px;padding:12px 14px;">
        <div style="font-family:'Space Mono',monospace;font-size:.6rem;color:#475569;
            letter-spacing:.08em;margin-bottom:6px;">HESABIM</div>
        <div style="font-family:'Syne',sans-serif;font-weight:700;color:#e2e8f0;font-size:.9rem;">
            {u.get('name','Kullanıcı')}</div>
        <div style="font-family:'Space Mono',monospace;font-size:.6rem;color:#475569;margin-top:2px;">
            {u.get('email','')}</div>
        <div style="margin-top:8px;display:flex;align-items:center;gap:8px;">
            <span style="background:{rc}22;border:1px solid {rc}55;border-radius:4px;
                padding:2px 7px;font-family:'Space Mono',monospace;font-size:.6rem;color:{rc};">{rank}</span>
            <span style="font-family:'Space Mono',monospace;font-size:.6rem;color:#475569;">{xp:,} XP</span>
        </div>
    </div>""", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Çıkış", use_container_width=True, key="logout_btn"):
        _clear_remember()
        st.session_state.authenticated = False
        st.session_state.user = None
        st.rerun()
