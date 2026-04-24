"""BORSA ARENA — Quant & Social Hub v0.4"""
import streamlit as st

st.set_page_config(
    page_title="Borsa Arena",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About":"Borsa Arena v0.4 — Türkiye'nin Quant & Social Trading Platformu"},
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;700;800&display=swap');
.stApp{background:#0a0e1a;color:#e2e8f0;}
section[data-testid="stSidebar"]{background:#0d1220!important;border-right:1px solid #1e2d4a;}
[data-testid="metric-container"]{background:#111827;border:1px solid #1e2d4a;border-radius:8px;padding:12px;}
.stButton>button{background:linear-gradient(135deg,#00d4aa,#0066ff);color:white;border:none;
    border-radius:6px;font-family:'Space Mono',monospace;font-weight:700;letter-spacing:.05em;transition:all .2s;}
.stButton>button:hover{transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,212,170,.3);}
h1,h2,h3{font-family:'Syne',sans-serif!important;color:#f1f5f9!important;}
.stTabs [data-baseweb="tab-list"]{background:#111827;border-radius:8px;padding:4px;gap:4px;}
.stTabs [data-baseweb="tab"]{background:transparent;color:#64748b;border-radius:6px;
    font-family:'Space Mono',monospace;font-size:.8rem;}
.stTabs [aria-selected="true"]{background:#1e2d4a!important;color:#00d4aa!important;}
.stSelectbox>div>div,.stMultiSelect>div>div{background:#111827!important;border-color:#1e2d4a!important;}
[data-testid="stDataFrame"]{border:1px solid #1e2d4a;border-radius:8px;overflow:hidden;}
hr{border-color:#1e2d4a!important;}
::-webkit-scrollbar{width:6px;height:6px;}
::-webkit-scrollbar-track{background:#0a0e1a;}
::-webkit-scrollbar-thumb{background:#1e2d4a;border-radius:3px;}
code{color:#00d4aa;font-family:'Space Mono',monospace;}
[data-testid="stSidebarNav"]{display:none!important;}
.streamlit-expanderHeader{background:#111827!important;border:1px solid #1e2d4a!important;
    border-radius:6px!important;color:#e2e8f0!important;}
input[type="text"],input[type="password"],input[type="email"],textarea{
    background:#111827!important;color:#e2e8f0!important;border-color:#1e2d4a!important;}
</style>""", unsafe_allow_html=True)

for k,v in [("authenticated",False),("user",None),("page","dashboard")]:
    if k not in st.session_state:
        st.session_state[k] = v

from utils.auth import login_page, sidebar_user_menu
from pages import dashboard, strategy_lab, fantasy_lig, correlation, social, valuation

NAV = [
    ("🏠","Dashboard",        "dashboard"),
    ("🔬","Strateji Lab",     "strategy_lab"),
    ("💎","Değerleme",        "valuation"),
    ("⚽","Fantezi Lig",      "fantasy_lig"),
    ("🌡️","Korelasyon",       "correlation"),
    ("📡","Sosyal Sinyal",    "social"),
]

if not st.session_state.authenticated:
    login_page()
else:
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:18px 0 14px 0;">
            <div style="font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:800;
                background:linear-gradient(90deg,#00d4aa,#0066ff);
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                background-clip:text;">📊 BORSA ARENA</div>
            <div style="font-family:'Space Mono',monospace;font-size:.5rem;
                color:#334155;letter-spacing:.18em;margin-top:3px;">QUANT & SOCIAL HUB v0.4</div>
        </div>
        <hr style="border-color:#1e2d4a;margin:0 0 10px 0;">""", unsafe_allow_html=True)

        for icon, label, key in NAV:
            active = st.session_state.page == key
            if st.button(f"{icon}  {label}", key=f"nav_{key}",
                         use_container_width=True, type="primary" if active else "secondary"):
                st.session_state.page = key
                st.rerun()

        st.markdown('<hr style="border-color:#1e2d4a;margin:10px 0;">', unsafe_allow_html=True)
        sidebar_user_menu()

        st.markdown("""
        <div style="position:fixed;bottom:10px;left:8px;right:8px;
            font-family:'Space Mono',monospace;font-size:.48rem;
            color:#1e293b;text-align:center;line-height:1.6;">
            ⚠️ Yatırım tavsiyesi değildir.<br>Veriler bilgilendirme amaçlıdır.
        </div>""", unsafe_allow_html=True)

    dispatch = {
        "dashboard":    dashboard.render,
        "strategy_lab": strategy_lab.render,
        "valuation":    valuation.render,
        "fantasy_lig":  fantasy_lig.render,
        "correlation":  correlation.render,
        "social":       social.render,
    }
    dispatch.get(st.session_state.page, dashboard.render)()
