"""Nomi italiani di Gran Premi e sessioni."""
from __future__ import annotations

NOMI_SESSIONI = {
    "Practice 1": "Prove Libere 1", "Practice 2": "Prove Libere 2", "Practice 3": "Prove Libere 3",
    "Qualifying": "Qualifiche", "Sprint Qualifying": "Qualifiche Sprint", "Sprint Shootout": "Qualifiche Sprint",
    "Sprint": "Sprint", "Race": "Gara",
}

NOMI_GP = {
    "Australian Grand Prix": "GP d'Australia", "Chinese Grand Prix": "GP di Cina",
    "Japanese Grand Prix": "GP del Giappone", "Bahrain Grand Prix": "GP del Bahrain",
    "Saudi Arabian Grand Prix": "GP dell'Arabia Saudita", "Miami Grand Prix": "GP di Miami",
    "Emilia Romagna Grand Prix": "GP dell'Emilia-Romagna", "Monaco Grand Prix": "GP di Monaco",
    "Spanish Grand Prix": "GP di Spagna", "Barcelona-Catalunya Grand Prix": "GP di Barcellona-Catalogna",
    "Canadian Grand Prix": "GP del Canada", "Austrian Grand Prix": "GP d'Austria",
    "British Grand Prix": "GP di Gran Bretagna", "Belgian Grand Prix": "GP del Belgio",
    "Hungarian Grand Prix": "GP d'Ungheria", "Dutch Grand Prix": "GP d'Olanda",
    "Italian Grand Prix": "GP d'Italia", "Azerbaijan Grand Prix": "GP dell'Azerbaigian",
    "Singapore Grand Prix": "GP di Singapore", "United States Grand Prix": "GP degli Stati Uniti",
    "Mexico City Grand Prix": "GP di Città del Messico", "Mexican Grand Prix": "GP del Messico",
    "São Paulo Grand Prix": "GP di San Paolo", "Brazilian Grand Prix": "GP del Brasile",
    "Las Vegas Grand Prix": "GP di Las Vegas", "Qatar Grand Prix": "GP del Qatar",
    "Abu Dhabi Grand Prix": "GP di Abu Dhabi", "French Grand Prix": "GP di Francia",
    "German Grand Prix": "GP di Germania", "Russian Grand Prix": "GP di Russia",
    "Portuguese Grand Prix": "GP del Portogallo", "Turkish Grand Prix": "GP di Turchia",
    "Tuscan Grand Prix": "GP della Toscana", "Styrian Grand Prix": "GP di Stiria",
    "70th Anniversary Grand Prix": "GP del 70° Anniversario", "Eifel Grand Prix": "GP dell'Eifel",
    "Sakhir Grand Prix": "GP di Sakhir", "Madrid Grand Prix": "GP di Madrid",
}


def nome_gp(nome_en: str) -> str:
    return NOMI_GP.get(nome_en, nome_en)


def tipo_sessione(nome: str) -> str:
    if nome in ("Race", "Sprint"):
        return "gara"
    if nome in ("Qualifying", "Sprint Qualifying", "Sprint Shootout"):
        return "qualifica"
    return "prove"
