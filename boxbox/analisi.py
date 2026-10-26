"""Tutti i calcoli e i 'racconti' in italiano.

Questo modulo non dipende da Streamlit né da FastF1: lavora su normali DataFrame
pandas, così si può testare e riusare (per esempio in una futura API).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .testi import fmt_num, fmt_secondi, fmt_tempo, nome_mescola, posizione

# --------------------------------------------------------------------------- utilità


def _sec(td) -> float:
    return td.total_seconds() if pd.notna(td) else np.nan


def nomi(ris: pd.DataFrame) -> dict[str, str]:
    """Sigla -> nome completo (es. 'LEC' -> 'Charles Leclerc')."""
    if ris is None or ris.empty or "Abbreviation" not in ris:
        return {}
    return {r.Abbreviation: (r.FullName if isinstance(r.FullName, str) and r.FullName else r.Abbreviation)
            for r in ris.itertuples()}


def squadre(ris: pd.DataFrame) -> dict[str, str]:
    if ris is None or ris.empty:
        return {}
    return {r.Abbreviation: r.TeamName for r in ris.itertuples()}


def colori(ris: pd.DataFrame) -> dict[str, str]:
    out = {}
    for r in ris.itertuples():
        c = str(getattr(r, "TeamColor", "") or "").strip().lstrip("#")
        out[r.Abbreviation] = f"#{c}" if len(c) == 6 else "#888888"
    return out


def _numerico(serie: pd.Series) -> pd.Series:
    return serie.astype(str).str.fullmatch(r"\d+")


def migliori_giri(giri: pd.DataFrame) -> pd.DataFrame:
    g = giri.dropna(subset=["LapTime"]).copy()
    if g.empty:
        return pd.DataFrame(columns=["Driver", "Sec", "LapNumber", "Compound"])
    g["Sec"] = g["LapTime"].dt.total_seconds()
    best = g.loc[g.groupby("Driver")["Sec"].idxmin(), ["Driver", "Sec", "LapNumber", "Compound"]]
    return best.sort_values("Sec").reset_index(drop=True)


def ordine_piloti(ris: pd.DataFrame, giri: pd.DataFrame, tipo: str) -> list[str]:
    """Piloti ordinati: per risultato in gara/qualifica, per miglior giro nelle prove."""
    con_giri = set(giri["Driver"].dropna().unique())
    if tipo != "prove" and not ris.empty and ris["Position"].notna().any():
        ordine = [d for d in ris.sort_values("Position")["Abbreviation"] if d in con_giri]
    else:
        ordine = list(migliori_giri(giri)["Driver"])
    return ordine + sorted(con_giri - set(ordine))


# --------------------------------------------------------------------------- classifiche


def _partenza(griglia) -> str:
    if pd.isna(griglia) or griglia == 0:
        return "dalla pit lane"
    if griglia == 1:
        return "dalla pole position"
    return f"dalla {int(griglia)}ª posizione"


def classifica_gara(ris: pd.DataFrame) -> pd.DataFrame:
    r = ris.sort_values("Position")
    n = len(r)
    griglia = r["GridPosition"].where(r["GridPosition"] > 0, n)
    guad = (griglia - r["Position"]).where(_numerico(r["ClassifiedPosition"]))
    return pd.DataFrame({
        "Pos": [posizione(p) if c else "Rit." for p, c in zip(r["Position"], _numerico(r["ClassifiedPosition"]))],
        "Pilota": r["FullName"],
        "Squadra": r["TeamName"],
        "Partenza": [("Pit lane" if g == 0 else posizione(g)) for g in r["GridPosition"]],
        "Posizioni +/-": [("" if pd.isna(x) else f"{int(x):+d}") for x in guad],
        "Punti": [fmt_num(p) if pd.notna(p) else "0" for p in r["Points"]],
    })


def _tempo_qualifica(riga) -> float:
    for col in ("Q3", "Q2", "Q1"):
        if col in riga and pd.notna(riga[col]):
            return _sec(riga[col])
    return np.nan


def classifica_qualifica(ris: pd.DataFrame) -> pd.DataFrame:
    r = ris.sort_values("Position")
    tempi = r.apply(_tempo_qualifica, axis=1)
    pole = tempi.iloc[0] if len(tempi) else np.nan
    return pd.DataFrame({
        "Pos": [posizione(p) for p in r["Position"]],
        "Pilota": r["FullName"],
        "Squadra": r["TeamName"],
        **{q: [fmt_tempo(_sec(t)) for t in r[q]] for q in ("Q1", "Q2", "Q3") if q in r},
        "Distacco": ["" if i == 0 else fmt_secondi(t - pole, segno=True) for i, t in enumerate(tempi)],
    })


def classifica_prove(giri: pd.DataFrame, ris: pd.DataFrame) -> pd.DataFrame:
    best = migliori_giri(giri)
    if best.empty:
        return best
    n, sq = nomi(ris), squadre(ris)
    conteggio = giri.groupby("Driver")["LapNumber"].count()
    primo = best["Sec"].iloc[0]
    return pd.DataFrame({
        "Pos": [f"{i + 1}°" for i in range(len(best))],
        "Pilota": [n.get(d, d) for d in best["Driver"]],
        "Squadra": [sq.get(d, "") for d in best["Driver"]],
        "Miglior giro": [fmt_tempo(s) for s in best["Sec"]],
        "Distacco": ["" if i == 0 else fmt_secondi(s - primo, segno=True) for i, s in enumerate(best["Sec"])],
        "Gomma": [nome_mescola(c) for c in best["Compound"]],
        "Giri fatti": [int(conteggio.get(d, 0)) for d in best["Driver"]],
    })


# --------------------------------------------------------------------------- racconti di sessione


def racconto_gara(ris: pd.DataFrame, giri: pd.DataFrame) -> list[str]:
    r = ris.dropna(subset=["Position"]).sort_values("Position")
    if r.empty:
        return ["I risultati di questa sessione non sono disponibili."]
    n = nomi(ris)
    frasi = []
    v = r.iloc[0]
    frasi.append(f"🏆 Ha vinto **{v.FullName}** ({v.TeamName}), partito {_partenza(v.GridPosition)}.")
    if len(r) >= 3:
        frasi.append(f"🥈 Sul podio con lui **{r.iloc[1].FullName}** e **{r.iloc[2].FullName}**.")

    classificati = r[_numerico(r["ClassifiedPosition"])].copy()
    if not classificati.empty:
        griglia = classificati["GridPosition"].where(classificati["GridPosition"] > 0, len(ris))
        classificati["Guadagno"] = griglia - classificati["Position"]
        top = classificati.sort_values("Guadagno", ascending=False).iloc[0]
        if top.Guadagno >= 3:
            frasi.append(f"📈 La rimonta migliore è di **{top.FullName}**: da {posizione(griglia[top.name])} "
                         f"a {posizione(top.Position)}, {int(top.Guadagno)} posizioni guadagnate.")
        peggio = classificati.sort_values("Guadagno").iloc[0]
        if peggio.Guadagno <= -3:
            frasi.append(f"📉 Giornata difficile per **{peggio.FullName}**: partito {posizione(griglia[peggio.name])}, "
                         f"ha chiuso {posizione(peggio.Position)}.")

    ritirati = ris[~_numerico(ris["ClassifiedPosition"])]
    if not ritirati.empty:
        elenco = ", ".join(ritirati["FullName"].astype(str))
        frasi.append(f"🛑 Non hanno visto il traguardo: {elenco}.")

    best = migliori_giri(giri)
    if not best.empty:
        g = best.iloc[0]
        frasi.append(f"⏱️ Giro più veloce di **{n.get(g.Driver, g.Driver)}**: {fmt_tempo(g.Sec)} "
                     f"al giro {int(g.LapNumber)}, con gomma {nome_mescola(g.Compound).lower()}.")

    soste = giri.groupby("Driver")["Stint"].nunique().sub(1)
    soste = soste[soste.index.isin(r[_numerico(r["ClassifiedPosition"])]["Abbreviation"])]
    if not soste.empty:
        comune = int(soste.mode().iloc[0])
        quanti = int((soste == comune).sum())
        testo = "nessuna sosta" if comune == 0 else ("una sosta" if comune == 1 else f"{comune} soste")
        frasi.append(f"🛞 La strategia più usata: {testo} ai box ({quanti} piloti su {len(soste)} arrivati).")
    return frasi


def racconto_qualifica(ris: pd.DataFrame) -> list[str]:
    r = ris.dropna(subset=["Position"]).sort_values("Position")
    if r.empty:
        return ["I risultati di questa sessione non sono disponibili."]
    frasi = []
    p = r.iloc[0]
    t1 = _tempo_qualifica(p)
    frasi.append(f"🥇 Pole position per **{p.FullName}** ({p.TeamName}) con {fmt_tempo(t1)}.")
    if len(r) >= 2:
        s = r.iloc[1]
        gap = _tempo_qualifica(s) - t1
        if pd.notna(gap):
            commento = " Un soffio!" if gap < 0.05 else (" Un distacco netto." if gap > 0.3 else "")
            frasi.append(f"🥈 Secondo **{s.FullName}**, staccato di {fmt_secondi(gap)}.{commento}")
    if "Q2" in r and "Q1" in r:
        fuori_q1 = r[r["Q1"].notna() & r["Q2"].isna()]["FullName"].tolist()
        if fuori_q1:
            frasi.append(f"❌ Eliminati in Q1: {', '.join(fuori_q1)}.")
    if "Q3" in r and "Q2" in r:
        fuori_q2 = r[r["Q2"].notna() & r["Q3"].isna()]["FullName"].tolist()
        if fuori_q2:
            frasi.append(f"❌ Eliminati in Q2: {', '.join(fuori_q2)}.")
    return frasi


def racconto_prove(giri: pd.DataFrame, ris: pd.DataFrame) -> list[str]:
    best = migliori_giri(giri)
    if best.empty:
        return ["Nessun giro cronometrato in questa sessione."]
    n = nomi(ris)
    p = best.iloc[0]
    frasi = [f"⏱️ Il più veloce è stato **{n.get(p.Driver, p.Driver)}** con {fmt_tempo(p.Sec)} "
             f"(gomma {nome_mescola(p.Compound).lower()})."]
    if len(best) >= 3:
        frasi.append(f"Dietro di lui **{n.get(best.iloc[1].Driver)}** "
                     f"({fmt_secondi(best.iloc[1].Sec - p.Sec, True)}) e **{n.get(best.iloc[2].Driver)}** "
                     f"({fmt_secondi(best.iloc[2].Sec - p.Sec, True)}).")
    piu_giri = giri.groupby("Driver")["LapNumber"].count().sort_values(ascending=False)
    frasi.append(f"🔁 Il più instancabile: **{n.get(piu_giri.index[0], piu_giri.index[0])}** con {int(piu_giri.iloc[0])} giri.")
    frasi.append("ℹ️ Attenzione: nelle prove libere ogni squadra lavora sul suo programma (benzina, gomme, "
                 "assetto), quindi la classifica conta poco.")
    return frasi


def racconto_meteo(meteo: pd.DataFrame) -> str | None:
    if meteo is None or meteo.empty or "AirTemp" not in meteo:
        return None
    pioggia = bool(meteo.get("Rainfall", pd.Series([False])).fillna(False).astype(bool).any())
    return (f"🌡️ Aria {fmt_num(meteo['AirTemp'].mean())} °C, asfalto {fmt_num(meteo['TrackTemp'].mean())} °C · "
            + ("🌧️ è piovuto durante la sessione" if pioggia else "☀️ niente pioggia"))


# --------------------------------------------------------------------------- sfida tra piloti


def _prepara(tel: pd.DataFrame) -> pd.DataFrame:
    t = tel.copy()
    t["Tempo"] = t["Time"].dt.total_seconds()
    t = t.dropna(subset=["Distance", "Tempo", "Speed"]).sort_values("Distance")
    t = t.drop_duplicates("Distance")
    t["Brake"] = t["Brake"].astype(float)
    t["Throttle"] = t["Throttle"].clip(0, 100)
    return t


def allinea(tel_a: pd.DataFrame, tel_b: pd.DataFrame, passo: float = 2.0) -> pd.DataFrame:
    """Porta due giri sulla stessa 'griglia' di metri, per confrontarli punto per punto.

    Delta > 0 vuol dire che il pilota A è davanti in quel punto.
    """
    a, b = _prepara(tel_a), _prepara(tel_b)
    fine = min(a["Distance"].iloc[-1], b["Distance"].iloc[-1])
    d = np.arange(0.0, fine, passo)
    out = {"Distanza": d}
    canali = {"Tempo": "Tempo", "Speed": "Velocita", "Throttle": "Gas", "Brake": "Freno", "nGear": "Marcia"}
    for suff, t in (("A", a), ("B", b)):
        x = t["Distance"].to_numpy()
        for col, nome in canali.items():
            out[f"{nome}_{suff}"] = np.interp(d, x, t[col].to_numpy(dtype=float))
    for col in ("X", "Y"):
        if col in a:
            out[col] = np.interp(d, a["Distance"].to_numpy(), a[col].to_numpy(dtype=float))
    df = pd.DataFrame(out)
    for s in ("A", "B"):
        df[f"Freno_{s}"] = df[f"Freno_{s}"] > 0.5
        df[f"Marcia_{s}"] = df[f"Marcia_{s}"].round().astype(int)
    df["Delta"] = df["Tempo_B"] - df["Tempo_A"]
    return df


def zone(df: pd.DataFrame, curve: pd.DataFrame | None, n_tratti: int = 12) -> pd.DataFrame:
    """Divide il giro in zone (una per curva, se conosciamo le curve) e misura chi guadagna dove."""
    fine = float(df["Distanza"].iloc[-1])
    if curve is not None and len(curve) >= 3 and "Distance" in curve:
        c = curve.sort_values("Distance")
        c = c[(c["Distance"] > 0) & (c["Distance"] < fine)]
        dist = c["Distance"].to_numpy(dtype=float)
        etichette = [f"Curva {int(nr)}{str(l or '').strip()}" for nr, l in zip(c["Number"], c.get("Letter", [""] * len(c)))]
        confini = [0.0, *((dist[:-1] + dist[1:]) / 2), fine]
        centri = list(dist)
    else:
        confini = list(np.linspace(0, fine, n_tratti + 1))
        etichette = [f"Tratto {i + 1}" for i in range(n_tratti)]
        centri = [(confini[i] + confini[i + 1]) / 2 for i in range(n_tratti)]

    righe = []
    for et, ini, fin, centro in zip(etichette, confini[:-1], confini[1:], centri):
        seg = df[(df["Distanza"] >= ini) & (df["Distanza"] <= fin)]
        if len(seg) < 3:
            continue
        dt_a = seg["Tempo_A"].iloc[-1] - seg["Tempo_A"].iloc[0]
        dt_b = seg["Tempo_B"].iloc[-1] - seg["Tempo_B"].iloc[0]

        def prima_frenata(s):
            m = seg.loc[seg[f"Freno_{s}"], "Distanza"]
            return float(m.iloc[0]) if len(m) else np.nan

        righe.append({
            "Zona": et, "Inizio": ini, "Fine": fin, "Centro": centro,
            "Guadagno_A": dt_b - dt_a,
            "VMin_A": seg["Velocita_A"].min(), "VMin_B": seg["Velocita_B"].min(),
            "VMax_A": seg["Velocita_A"].max(), "VMax_B": seg["Velocita_B"].max(),
            "Frenata_A": prima_frenata("A"), "Frenata_B": prima_frenata("B"),
        })
    return pd.DataFrame(righe)


def tipo_zona(vmin: float) -> str:
    if vmin < 130:
        return "lente"
    if vmin < 200:
        return "medie"
    return "veloci"


def perche(z: pd.Series, a: str, b: str) -> str:
    """Spiega in parole semplici perché il pilota più rapido guadagna in una zona."""
    vince_a = z["Guadagno_A"] > 0
    w, l = ("A", "B") if vince_a else ("B", "A")
    motivi = []
    if z[f"VMin_{w}"] - z[f"VMin_{l}"] >= 3:
        motivi.append(f"passa più veloce nel punto più lento ({fmt_num(z[f'VMin_{w}'])} contro "
                      f"{fmt_num(z[f'VMin_{l}'])} km/h)")
    if pd.notna(z[f"Frenata_{w}"]) and pd.notna(z[f"Frenata_{l}"]):
        metri = z[f"Frenata_{w}"] - z[f"Frenata_{l}"]
        if metri >= 5:
            motivi.append(f"frena circa {fmt_num(metri)} metri più tardi")
    if z[f"VMax_{w}"] - z[f"VMax_{l}"] >= 3:
        motivi.append(f"arriva più veloce in fondo al rettilineo ({fmt_num(z[f'VMax_{w}'])} contro "
                      f"{fmt_num(z[f'VMax_{l}'])} km/h)")
    if not motivi:
        return "la differenza è piccola e distribuita: guida un po' più pulita in tutta la zona"
    return _elenco(motivi)


def _elenco(voci: list[str]) -> str:
    return voci[0] if len(voci) == 1 else ", ".join(voci[:-1]) + " e " + voci[-1]


def racconto_sfida(df: pd.DataFrame, zn: pd.DataFrame, a: str, b: str, nome_a: str, nome_b: str,
                   tempo_a: float, tempo_b: float) -> list[str]:
    frasi = []
    diff = tempo_b - tempo_a
    if abs(diff) < 0.0005:
        frasi.append(f"Incredibile: **{nome_a}** e **{nome_b}** hanno fatto lo stesso tempo al millesimo, "
                     f"{fmt_tempo(tempo_a)}.")
        veloce, lento, nv, nl, segno = a, b, nome_a, nome_b, 1
    else:
        a_avanti = diff > 0
        veloce, lento = (a, b) if a_avanti else (b, a)
        nv, nl = (nome_a, nome_b) if a_avanti else (nome_b, nome_a)
        tv, tl = (tempo_a, tempo_b) if a_avanti else (tempo_b, tempo_a)
        segno = 1 if a_avanti else -1
        frasi.append(f"🏁 **{nv}** ha girato più forte: {fmt_tempo(tv)} contro {fmt_tempo(tl)}, "
                     f"cioè **{fmt_secondi(abs(diff))}** in meno sul giro.")

    if not zn.empty:
        g = zn.assign(G=zn["Guadagno_A"] * segno)  # G > 0: guadagna il più veloce
        for _, z in g[g["G"] > 0.01].sort_values("G", ascending=False).head(3).iterrows():
            frasi.append(f"✅ In **{z.Zona}** {nv.split()[-1]} guadagna {fmt_secondi(z.G)}: {perche(z, a, b)}.")
        for _, z in g[g["G"] < -0.01].sort_values("G").head(2).iterrows():
            frasi.append(f"↩️ {nl.split()[-1]} però si rifà in **{z.Zona}** (+{fmt_secondi(-z.G)}): {perche(z, a, b)}.")

        g["Tipo"] = np.minimum(g["VMin_A"], g["VMin_B"]).map(tipo_zona)
        per_tipo = g.groupby("Tipo")["G"].sum()
        forti_v = [t for t, v in per_tipo.items() if v > 0.02]
        forti_l = [t for t, v in per_tipo.items() if v < -0.02]
        if forti_v and forti_l:
            frasi.append(f"🧭 In sintesi: {nv.split()[-1]} è più forte nelle curve {_elenco(forti_v)}, "
                         f"{nl.split()[-1]} in quelle {_elenco(forti_l)}.")
        elif forti_v and not forti_l and len(forti_v) >= 2:
            frasi.append(f"🧭 In sintesi: {nv.split()[-1]} è davanti un po' ovunque, nelle curve "
                         f"{_elenco(forti_v)}.")

    vmax = {a: df["Velocita_A"].max(), b: df["Velocita_B"].max()}
    pieno = {a: (df["Gas_A"] >= 98).mean() * 100, b: (df["Gas_B"] >= 98).mean() * 100}
    frasi.append(f"🚀 Velocità massima: {nome_a.split()[-1]} {fmt_num(vmax[a])} km/h, "
                 f"{nome_b.split()[-1]} {fmt_num(vmax[b])} km/h.")
    frasi.append(f"🦶 Acceleratore a tavoletta per il {fmt_num(pieno[a])}% della pista ({nome_a.split()[-1]}) "
                 f"e il {fmt_num(pieno[b])}% ({nome_b.split()[-1]}).")
    return frasi


# --------------------------------------------------------------------------- gomme e strategia


def strategie(giri: pd.DataFrame) -> pd.DataFrame:
    g = giri.dropna(subset=["Stint"])
    s = (g.groupby(["Driver", "Stint"])
         .agg(Mescola=("Compound", "first"), Inizio=("LapNumber", "min"), Fine=("LapNumber", "max"),
              Giri=("LapNumber", "count"), Usura=("TyreLife", "min"))
         .reset_index())
    s["Usata"] = s["Usura"].fillna(1) > 2  # gomma già usata in precedenza
    return s


def giri_puliti(giri: pd.DataFrame) -> pd.DataFrame:
    """Solo i giri 'normali': niente soste, niente primo giro, niente safety car, niente giri lenti strani."""
    g = giri[giri["LapTime"].notna() & giri["PitInTime"].isna() & giri["PitOutTime"].isna()
             & (giri["LapNumber"] > 1)].copy()
    if "TrackStatus" in g:
        g = g[g["TrackStatus"].astype(str).str.fullmatch(r"1+")]
    g["Sec"] = g["LapTime"].dt.total_seconds()
    if g.empty:
        return g
    return g[g["Sec"] <= g["Sec"].min() * 1.07]


def passo(puliti: pd.DataFrame) -> pd.DataFrame:
    p = puliti.groupby("Driver")["Sec"].agg(Mediana="median", Giri="count").reset_index()
    p = p[p["Giri"] >= 5].sort_values("Mediana").reset_index(drop=True)
    p["Distacco"] = p["Mediana"] - p["Mediana"].min()
    return p


def degrado(puliti: pd.DataFrame, min_giri: int = 6) -> pd.DataFrame:
    righe = []
    for (d, st), g in puliti.groupby(["Driver", "Stint"]):
        g = g.dropna(subset=["TyreLife"])
        if len(g) < min_giri:
            continue
        pendenza = np.polyfit(g["TyreLife"].to_numpy(float), g["Sec"].to_numpy(float), 1)[0]
        righe.append({"Driver": d, "Stint": int(st), "Mescola": g["Compound"].iloc[0],
                      "Giri": len(g), "PerditaGiro": pendenza})
    return pd.DataFrame(righe)


def racconto_degrado(deg: pd.DataFrame, n: dict[str, str]) -> list[str]:
    if deg.empty:
        return []
    frasi = []
    per_mescola = deg.groupby("Mescola")["PerditaGiro"].median()
    for m, v in per_mescola.sort_values().items():
        if v <= 0.01:
            commento = "praticamente nessun calo (la benzina che si consuma compensa l'usura)"
        else:
            commento = f"in media perdeva circa {fmt_secondi(v)} a giro"
        frasi.append(f"🛞 Gomma **{nome_mescola(m).lower()}**: {commento}.")
    peggiore = deg.sort_values("PerditaGiro", ascending=False).iloc[0]
    if peggiore.PerditaGiro > 0.05:
        frasi.append(f"⚠️ Il calo più evidente: **{n.get(peggiore.Driver, peggiore.Driver)}** con le "
                     f"{nome_mescola(peggiore.Mescola).lower()} (stint {peggiore.Stint}), "
                     f"{fmt_secondi(peggiore.PerditaGiro)} a giro.")
    return frasi


def racconto_passo(pa: pd.DataFrame, n: dict[str, str], ordine_arrivo: list[str]) -> list[str]:
    if pa.empty:
        return []
    frasi = [f"⚡ Il passo gara migliore è di **{n.get(pa.Driver.iloc[0], pa.Driver.iloc[0])}**: "
             f"in media {fmt_tempo(pa.Mediana.iloc[0])} a giro."]
    if len(pa) >= 2:
        frasi.append(f"Il secondo, **{n.get(pa.Driver.iloc[1], pa.Driver.iloc[1])}**, era {fmt_secondi(pa.Distacco.iloc[1])} "
                     f"più lento a giro.")
    # chi ha raccolto meno di quanto valeva il suo passo
    rango_passo = {d: i for i, d in enumerate(pa["Driver"])}
    rango_arrivo = {d: i for i, d in enumerate(ordine_arrivo)}
    sfortunati = [(rango_arrivo[d] - rango_passo[d], d) for d in rango_passo if d in rango_arrivo]
    sfortunati.sort(reverse=True)
    if sfortunati and sfortunati[0][0] >= 4:
        d = sfortunati[0][1]
        frasi.append(f"🤔 **{n.get(d, d)}** aveva il {rango_passo[d] + 1}° passo ma è arrivato "
                     f"{rango_arrivo[d] + 1}°: strategia, traffico o qualche problema gli sono costati posizioni.")
    return frasi
