"""Grafici Plotly, pensati per essere letti anche da chi non ha mai visto una telemetria."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .testi import colore_mescola, fmt_num, fmt_secondi, fmt_tempo, nome_mescola

GRIGIO = "rgba(128,128,128,0.45)"


def _cognome(nome: str) -> str:
    return nome.split()[-1]


def colori_sfida(ca: str, cb: str) -> tuple[str, str, str]:
    """Se i due piloti sono compagni di squadra, il secondo va tratteggiato."""
    return ca, cb, ("dot" if ca.lower() == cb.lower() else "solid")


def _segni_curve(fig, curve, righe: int, y_testo: float, riga_testo: int):
    if curve is None or curve.empty:
        return
    for c in curve.itertuples():
        for r in range(1, righe + 1):
            fig.add_vline(x=c.Distance, line_width=1, line_dash="dot", line_color=GRIGIO, row=r, col=1)
    fig.add_trace(go.Scatter(
        x=curve["Distance"], y=[y_testo] * len(curve), mode="text",
        text=[f"C{int(n)}{(l or '').strip()}" for n, l in zip(curve["Number"], curve.get("Letter", [""] * len(curve)))],
        textfont=dict(size=10, color="gray"), hoverinfo="skip", showlegend=False), row=riga_testo, col=1)


def confronto_telemetria(df: pd.DataFrame, nome_a: str, nome_b: str, ca: str, cb: str,
                         curve: pd.DataFrame | None) -> go.Figure:
    ca, cb, tratto_b = colori_sfida(ca, cb)
    a, b = _cognome(nome_a), _cognome(nome_b)
    fig = make_subplots(
        rows=5, cols=1, shared_xaxes=True, vertical_spacing=0.035,
        row_heights=[0.2, 0.32, 0.18, 0.1, 0.2],
        subplot_titles=(f"Distacco: sopra lo zero è davanti {a}, sotto è davanti {b}",
                        "Velocità (km/h)", "Acceleratore (%)", "Freno", "Marcia"))
    x = df["Distanza"]
    # distacco
    fig.add_trace(go.Scatter(x=x, y=df["Delta"].clip(lower=0), fill="tozeroy", mode="none",
                             fillcolor=ca, opacity=0.6, name=f"{a} davanti", hoverinfo="skip"), row=1, col=1)
    fig.add_trace(go.Scatter(x=x, y=df["Delta"].clip(upper=0), fill="tozeroy", mode="none",
                             fillcolor=cb, name=f"{b} davanti", hoverinfo="skip"), row=1, col=1)
    fig.add_trace(go.Scatter(x=x, y=df["Delta"], mode="lines", line=dict(color="gray", width=1),
                             name="Distacco", showlegend=False,
                             hovertemplate="Distacco: %{y:+.3f} s<extra></extra>"), row=1, col=1)
    # canali
    canali = [("Velocita", 2, "%{y:.0f} km/h", "linear"), ("Gas", 3, "%{y:.0f}%", "linear"),
              ("Freno", 4, None, "hv"), ("Marcia", 5, "%{y}ª", "hv")]
    for nome, col, (s, colore, dash) in [(nome_a, "A", ("A", ca, "solid")), (nome_b, "B", ("B", cb, tratto_b))]:
        for canale, riga, fmt, forma in canali:
            y = df[f"{canale}_{s}"].astype(float)
            fig.add_trace(go.Scatter(
                x=x, y=y, mode="lines", line=dict(color=colore, width=2 if canale == "Velocita" else 1.5,
                                                    dash=dash, shape=forma),
                name=_cognome(nome), legendgroup=s, showlegend=(canale == "Velocita"),
                hovertemplate=(f"{_cognome(nome)}: " + (fmt or "%{y}") + "<extra></extra>") if fmt else
                f"{_cognome(nome)}: %{{customdata}}<extra></extra>",
                customdata=np.where(y > 0.5, "frena", "—") if canale == "Freno" else None,
            ), row=riga, col=1)
    _segni_curve(fig, curve, 5, float(max(df["Velocita_A"].max(), df["Velocita_B"].max()) + 18), 2)
    fig.update_yaxes(tickvals=[0, 1], ticktext=["no", "sì"], range=[-0.1, 1.2], row=4, col=1)
    fig.update_yaxes(range=[0, 105], row=3, col=1)
    fig.update_xaxes(title_text="Metri dalla linea del traguardo", row=5, col=1)
    fig.update_layout(height=900, hovermode="x unified", margin=dict(l=10, r=10, t=40, b=10),
                      legend=dict(orientation="h", yanchor="bottom", y=1.03, x=0))
    return fig


def _ruota(x, y, gradi: float):
    t = np.deg2rad(gradi)
    return x * np.cos(t) - y * np.sin(t), x * np.sin(t) + y * np.cos(t)


def mappa_vantaggi(df: pd.DataFrame, zn: pd.DataFrame, nome_a: str, nome_b: str, ca: str, cb: str,
                   curve: pd.DataFrame | None, rotazione: float) -> go.Figure | None:
    """Il circuito colorato zona per zona con il colore di chi è più veloce."""
    if "X" not in df or zn.empty:
        return None
    ca, cb, _ = colori_sfida(ca, cb)
    if ca.lower() == cb.lower():
        cb = "#9E9E9E"
    x, y = _ruota(df["X"].to_numpy(), df["Y"].to_numpy(), rotazione)
    fig = go.Figure()
    for z in zn.itertuples():
        m = ((df["Distanza"] >= z.Inizio) & (df["Distanza"] <= z.Fine)).to_numpy()
        vince_a = z.Guadagno_A > 0
        colore = ca if vince_a else cb
        chi = _cognome(nome_a if vince_a else nome_b)
        fig.add_trace(go.Scatter(
            x=x[m], y=y[m], mode="lines", line=dict(color=colore, width=7), showlegend=False,
            hovertemplate=f"<b>{z.Zona}</b><br>{chi} più veloce di {fmt_secondi(abs(z.Guadagno_A))}<extra></extra>"))
    for nome, colore in ((nome_a, ca), (nome_b, cb)):
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", line=dict(color=colore, width=7),
                                 name=f"Più veloce {_cognome(nome)}"))
    if curve is not None and not curve.empty and {"X", "Y"} <= set(curve.columns):
        cx, cy = _ruota(curve["X"].to_numpy(float), curve["Y"].to_numpy(float), rotazione)
        fig.add_trace(go.Scatter(x=cx, y=cy, mode="text", text=[str(int(n)) for n in curve["Number"]],
                                 textfont=dict(size=11, color="gray"), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=[x[0]], y=[y[0]], mode="markers+text", text=["  Traguardo"],
                             textposition="middle right", marker=dict(symbol="square", size=10, color="gray"),
                             hoverinfo="skip", showlegend=False))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
    fig.update_layout(height=520, margin=dict(l=10, r=10, t=10, b=10),
                      legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0))
    return fig


def grafico_strategie(strat: pd.DataFrame, ordine: list[str], nomi: dict[str, str]) -> go.Figure:
    s = strat[strat["Driver"].isin(ordine)].copy()
    s["Etichetta"] = s["Driver"].map(lambda d: _cognome(nomi.get(d, d)))
    fig = go.Figure()
    for mescola, g in s.groupby("Mescola"):
        fig.add_trace(go.Bar(
            y=g["Etichetta"], x=g["Giri"], base=g["Inizio"] - 1, orientation="h",
            name=nome_mescola(mescola), marker=dict(color=colore_mescola(mescola), line=dict(color="#555", width=1)),
            text=[nome_mescola(mescola)[0] + ("*" if u else "") for u in g["Usata"]], textposition="inside",
            insidetextanchor="middle",
            customdata=np.stack([g["Inizio"], g["Fine"], g["Giri"]], axis=1),
            hovertemplate="%{y}: " + nome_mescola(mescola) + " dal giro %{customdata[0]} al %{customdata[1]} "
                          "(%{customdata[2]} giri)<extra></extra>"))
    etichette = [_cognome(nomi.get(d, d)) for d in ordine]
    fig.update_layout(barmode="overlay", height=max(320, 28 * len(ordine) + 80),
                      yaxis=dict(categoryorder="array", categoryarray=etichette[::-1]),
                      xaxis_title="Giro", margin=dict(l=10, r=10, t=10, b=10),
                      legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, title="Gomma: "))
    return fig


def grafico_passo(puliti: pd.DataFrame, piloti: list[str], nomi: dict[str, str], colori: dict[str, str]) -> go.Figure:
    fig = go.Figure()
    for d in piloti:
        g = puliti[puliti["Driver"] == d]
        if g.empty:
            continue
        fig.add_trace(go.Box(y=g["Sec"], name=_cognome(nomi.get(d, d)), marker_color=colori.get(d, "#888"),
                             boxpoints="all", jitter=0.4, pointpos=0, marker=dict(size=4, opacity=0.6),
                             customdata=[fmt_tempo(v) for v in g["Sec"]], text=g["LapNumber"].astype(int),
                             hovertemplate="Giro %{text}: %{customdata}<extra></extra>", showlegend=False))
    if not puliti.empty:
        lo, hi = puliti["Sec"].quantile(0.01), puliti["Sec"].quantile(0.99)
        passo_tick = 0.5 if hi - lo < 4 else 1.0
        tick = np.arange(np.floor(lo / passo_tick) * passo_tick, hi + passo_tick, passo_tick)
        fig.update_yaxes(tickvals=tick, ticktext=[fmt_tempo(t)[:-2] for t in tick])
    fig.update_layout(height=480, yaxis_title="Tempo sul giro (più in basso = più veloce)",
                      margin=dict(l=10, r=10, t=10, b=10))
    return fig


def grafico_posizioni(giri: pd.DataFrame, ordine: list[str], nomi: dict[str, str], colori: dict[str, str]) -> go.Figure:
    fig = go.Figure()
    visti: dict[str, int] = {}
    for d in ordine:
        g = giri[giri["Driver"] == d].dropna(subset=["Position"]).sort_values("LapNumber")
        if g.empty:
            continue
        col = colori.get(d, "#888")
        visti[col] = visti.get(col, 0) + 1
        fig.add_trace(go.Scatter(
            x=g["LapNumber"], y=g["Position"], mode="lines", name=_cognome(nomi.get(d, d)),
            line=dict(color=col, width=2, dash="dot" if visti[col] > 1 else "solid"),
            hovertemplate=_cognome(nomi.get(d, d)) + ": %{y}° al giro %{x}<extra></extra>"))
    n = max(len(ordine), 1)
    fig.update_yaxes(autorange="reversed", tickvals=list(range(1, n + 1)), title="Posizione")
    fig.update_xaxes(title="Giro")
    fig.update_layout(height=560, hovermode="closest", margin=dict(l=10, r=10, t=10, b=10))
    return fig
