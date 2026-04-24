"""
Grafik Üretici
--------------
Plotly tabanlı interaktif finansal grafikler.
Tema: Borsa Arena dark theme.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# ─── Renk Paleti ───
COLORS = {
    "bg":        "#0a0e1a",
    "bg2":       "#111827",
    "grid":      "#1e2d4a",
    "text":      "#94a3b8",
    "title":     "#e2e8f0",
    "green":     "#00d4aa",
    "red":       "#f87171",
    "blue":      "#60a5fa",
    "yellow":    "#f59e0b",
    "purple":    "#a78bfa",
    "orange":    "#fb923c",
    "candle_up": "#00d4aa",
    "candle_dn": "#f87171",
}

LAYOUT_BASE = dict(
    paper_bgcolor = COLORS["bg"],
    plot_bgcolor  = COLORS["bg2"],
    font          = dict(family="Space Mono, monospace", color=COLORS["text"], size=11),
    xaxis         = dict(gridcolor=COLORS["grid"], showgrid=True, zeroline=False),
    yaxis         = dict(gridcolor=COLORS["grid"], showgrid=True, zeroline=False),
    margin        = dict(l=40, r=20, t=40, b=40),
    legend        = dict(bgcolor="rgba(0,0,0,0)", bordercolor=COLORS["grid"]),
    hovermode     = "x unified",
)

def candlestick_chart(df: pd.DataFrame, title: str = "", indicators: list = None) -> go.Figure:
    """
    OHLC mum grafik + indikatör overlay/panel.
    
    Args:
        df: OHLCV + hesaplanmış indikatör kolonları
        title: Grafik başlığı
        indicators: ['sma_20', 'ema_50', 'bb_upper', ...]
    """
    if df.empty:
        return _empty_fig("Veri yok")
    
    indicators = indicators or []
    
    # Panel sayısı (volume + osilatörler)
    osc_inds  = [i for i in indicators if _is_oscillator(i)]
    row_count = 2 + (1 if osc_inds else 0)  # OHLC + Volume + Osc
    row_heights = [0.55, 0.2] + ([0.25] if osc_inds else [])
    
    fig = make_subplots(
        rows=row_count, cols=1, shared_xaxes=True,
        vertical_spacing=0.02, row_heights=row_heights,
    )
    
    # ── Mum Grafik ──
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["open"], high=df["high"],
        low=df["low"], close=df["close"],
        increasing_line_color=COLORS["candle_up"],
        decreasing_line_color=COLORS["candle_dn"],
        name="OHLC",
    ), row=1, col=1)
    
    # ── Overlay İndikatörler ──
    overlay_colors = [COLORS["blue"], COLORS["yellow"], COLORS["purple"],
                      COLORS["orange"], "#f472b6", "#34d399"]
    oi = 0
    for ind in indicators:
        if ind in df.columns and not _is_oscillator(ind):
            c = overlay_colors[oi % len(overlay_colors)]
            oi += 1
            fig.add_trace(go.Scatter(
                x=df.index, y=df[ind], name=ind,
                line=dict(color=c, width=1.5), opacity=0.9,
            ), row=1, col=1)
        
        # Bollinger Bantları fill
        if ind == "bb_upper" and "bb_lower" in df.columns and "bb_upper" in df.columns:
            fig.add_trace(go.Scatter(
                x=pd.concat([df.index.to_series(), df.index.to_series()[::-1]]),
                y=pd.concat([df["bb_upper"], df["bb_lower"][::-1]]),
                fill="toself", fillcolor="rgba(96,165,250,0.05)",
                line=dict(color="rgba(96,165,250,0.3)"),
                name="BB Band", showlegend=False,
            ), row=1, col=1)
    
    # ── Hacim ──
    colors_vol = [COLORS["candle_up"] if c >= o else COLORS["candle_dn"]
                  for c, o in zip(df["close"], df["open"])]
    fig.add_trace(go.Bar(
        x=df.index, y=df["volume"],
        marker_color=colors_vol, opacity=0.7, name="Hacim",
    ), row=2, col=1)
    
    # ── Osilatörler (Alt Panel) ──
    if osc_inds:
        osc_colors = [COLORS["green"], COLORS["blue"], COLORS["yellow"], COLORS["purple"]]
        for i, ind in enumerate(osc_inds):
            if ind in df.columns:
                c = osc_colors[i % len(osc_colors)]
                fig.add_trace(go.Scatter(
                    x=df.index, y=df[ind], name=ind,
                    line=dict(color=c, width=1.5),
                ), row=3, col=1)
        
        # RSI için aşırı alım/satım çizgileri
        if "rsi_14" in osc_inds or any("rsi" in i for i in osc_inds):
            for lvl, color in [(70, COLORS["red"]), (30, COLORS["green"]), (50, COLORS["grid"])]:
                fig.add_hline(y=lvl, row=3, col=1,
                              line_dash="dash", line_color=color, line_width=0.8, opacity=0.6)
    
    # ── Layout ──
    layout = {**LAYOUT_BASE,
              "title": dict(text=title, font=dict(size=15, color=COLORS["title"]), x=0),
              "xaxis_rangeslider_visible": False,
              "height": 600 if row_count <= 2 else 750}
    fig.update_layout(**layout)
    fig.update_yaxes(title_text="Fiyat", row=1, col=1)
    fig.update_yaxes(title_text="Hacim", row=2, col=1)
    
    return fig

def equity_curve_chart(equity: pd.Series, buy_hold: pd.Series = None,
                       title: str = "Strateji Equity Eğrisi") -> go.Figure:
    """Backtest equity eğrisi vs buy&hold karşılaştırma."""
    fig = go.Figure()
    
    # Strateji
    fig.add_trace(go.Scatter(
        x=equity.index, y=equity.values,
        fill="tozeroy", fillcolor="rgba(0,212,170,0.08)",
        line=dict(color=COLORS["green"], width=2),
        name="Strateji",
    ))
    
    # Buy & Hold
    if buy_hold is not None:
        fig.add_trace(go.Scatter(
            x=buy_hold.index, y=buy_hold.values,
            line=dict(color=COLORS["blue"], width=1.5, dash="dot"),
            name="Buy & Hold",
        ))
    
    fig.update_layout(**{**LAYOUT_BASE,
        "title": dict(text=title, font=dict(size=14, color=COLORS["title"])),
        "height": 320,
        "yaxis": {**LAYOUT_BASE["yaxis"], "title": "Portföy Değeri (₺)"},
    })
    
    return fig

def drawdown_chart(equity: pd.Series) -> go.Figure:
    """Maksimum drawdown grafiği."""
    rolling_max = equity.cummax()
    drawdown    = (equity - rolling_max) / rolling_max * 100
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=drawdown.index, y=drawdown.values,
        fill="tozeroy", fillcolor="rgba(248,113,113,0.15)",
        line=dict(color=COLORS["red"], width=1.5),
        name="Drawdown %",
    ))
    fig.update_layout(**{**LAYOUT_BASE,
        "title": dict(text="Drawdown %", font=dict(size=13, color=COLORS["title"])),
        "height": 220,
        "yaxis": {**LAYOUT_BASE["yaxis"], "title": "%"},
    })
    return fig

def correlation_heatmap(corr_matrix: pd.DataFrame, title: str = "Korelasyon Isı Haritası") -> go.Figure:
    """Korelasyon matrisi ısı haritası."""
    z    = corr_matrix.values
    text = [[f"{v:.2f}" for v in row] for row in z]
    
    fig = go.Figure(go.Heatmap(
        z=z, x=corr_matrix.columns, y=corr_matrix.index,
        text=text, texttemplate="%{text}", textfont=dict(size=9),
        colorscale=[[0,"#f87171"],[0.5,"#1e2d4a"],[1,"#00d4aa"]],
        zmid=0, zmin=-1, zmax=1,
        colorbar=dict(title="r", tickfont=dict(color=COLORS["text"])),
    ))
    
    fig.update_layout(**{**LAYOUT_BASE,
        "title": dict(text=title, font=dict(size=14, color=COLORS["title"])),
        "height": 520,
    })
    return fig

def bist_bar_chart(df: pd.DataFrame, x: str, y: str, color_col: str = None,
                   title: str = "") -> go.Figure:
    """BIST hisse performans bar grafiği."""
    if df.empty:
        return _empty_fig("Veri yok")
    
    if color_col and color_col in df.columns:
        colors = [COLORS["green"] if v >= 0 else COLORS["red"] for v in df[color_col]]
    else:
        colors = COLORS["blue"]
    
    fig = go.Figure(go.Bar(
        x=df[x], y=df[y], marker_color=colors, opacity=0.85, name=y,
    ))
    
    fig.update_layout(**{**LAYOUT_BASE,
        "title": dict(text=title, font=dict(size=13, color=COLORS["title"])),
        "height": 350,
    })
    return fig

def mini_sparkline(df: pd.DataFrame, symbol: str) -> go.Figure:
    """Küçük spark çizgisi."""
    fig = go.Figure(go.Scatter(
        x=df.index, y=df["close"],
        line=dict(color=COLORS["green"] if df["close"].iloc[-1] >= df["close"].iloc[0]
                  else COLORS["red"], width=1.5),
        fill="tozeroy",
        fillcolor="rgba(0,212,170,0.05)" if df["close"].iloc[-1] >= df["close"].iloc[0]
                  else "rgba(248,113,113,0.05)",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0), height=60,
        showlegend=False, xaxis=dict(visible=False), yaxis=dict(visible=False),
    )
    return fig

def _is_oscillator(col: str) -> bool:
    """Kolun alt panelde gösterilip gösterilmeyeceğini belirler."""
    osc_prefixes = ["rsi", "macd", "stoch", "cci", "willr", "mfi", "roc",
                    "mom", "ao", "uo", "dpo", "tsi", "cmf", "adosc"]
    col_lower = col.lower()
    return any(col_lower.startswith(p) for p in osc_prefixes)

def _empty_fig(msg: str = "Veri yok") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=msg, x=0.5, y=0.5, showarrow=False,
                       font=dict(color=COLORS["text"], size=14))
    fig.update_layout(**{**LAYOUT_BASE, "height": 300})
    return fig
