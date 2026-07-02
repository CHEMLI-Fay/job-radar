#!/usr/bin/env python3
"""
Collecte quotidienne d'offres d'emploi (France Travail + JSearch/Google Jobs)
matchées avec le profil de Fayçal CHEMLI (Data Scientist / AI Engineer junior).
Génère docs/data.json consommé par le dashboard.
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

import requests

# ---------------------------------------------------------------- profil
SEARCH_QUERIES = [
    "data scientist",
    "machine learning",
    "intelligence artificielle",
    "data analyst",
    "IA générative",
]

SKILL_KEYWORDS = {
    # mot-clé (minuscule) : poids
    "llm": 8, "rag": 8, "genai": 7, "ia générative": 7, "generative ai": 7,
    "vertex ai": 8, "gemini": 6, "gcp": 7, "google cloud": 7, "bigquery": 8,
    "looker": 9, "lookml": 9, "dataviz": 6, "data visualisation": 6,
    "streamlit": 5, "power bi": 4, "tableau": 4,
    "machine learning": 5, "deep learning": 5, "computer vision": 5,
    "pytorch": 5, "tensorflow": 4, "scikit": 4, "transformers": 5,
    "python": 4, "sql": 3, "docker": 3, "mlops": 6, "faiss": 6,
    "nlp": 4, "chatbot": 5, "agent": 4, "embeddings": 5,
    "data scientist": 6, "data analyst": 4, "ai engineer": 7,
}

JUNIOR_BONUS = ["junior", "débutant", "jeune diplômé", "graduate", "0-2 ans", "premier emploi", "entry level"]
SENIOR_PENALTY = ["senior", "confirmé", "5 ans", "7 ans", "8 ans", "10 ans", "lead ", "principal", "staff ", "head of", "manager"]

DAYS_BACK = int(os.environ.get("DAYS_BACK", "2"))  # offres publiées depuis N jours


def score_offer(title: str, description: str) -> tuple[int, list[str]]:
    text = f"{title} {description}".lower()
    score = 0
    matched = []
    for kw, w in SKILL_KEYWORDS.items():
        if kw in text:
            score += w
            matched.append(kw)
    tl = title.lower()
    if any(j in text for j in JUNIOR_BONUS):
        score += 10
    if any(s in tl for s in SENIOR_PENALTY):
        score -= 15
    return score, matched


# ---------------------------------------------------------------- France Travail
def fetch_france_travail() -> list[dict]:
    cid = os.environ.get("FT_CLIENT_ID")
    secret = os.environ.get("FT_CLIENT_SECRET")
    if not cid or not secret:
        print("[FT] Clés absentes, source ignorée.")
        return []
    try:
        r = requests.post(
            "https://entreprise.francetravail.fr/connexion/oauth2/access_token",
            params={"realm": "/partenaire"},
            data={
                "grant_type": "client_credentials",
                "client_id": cid,
                "client_secret": secret,
                "scope": "api_offresdemploiv2 o2dsoffre",
            },
            timeout=30,
        )
        r.raise_for_status()
        token = r.json()["access_token"]
    except Exception as e:
        print(f"[FT] Erreur auth: {e}")
        return []

    offers = []
    seen = set()
    for q in SEARCH_QUERIES:
        try:
            r = requests.get(
                "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "motsCles": q,
                    "typeContrat": "CDI",
                    # valeurs acceptées par l'API : 1, 3, 7, 14, 31
                    "publieeDepuis": str(next(v for v in (1, 3, 7, 14, 31) if v >= min(DAYS_BACK, 31))),
                    "range": "0-49",
                },
                timeout=30,
            )
            if r.status_code == 204:
                print(f"[FT] '{q}' -> aucun résultat")
                continue
            if r.status_code not in (200, 206):
                print(f"[FT] '{q}' -> HTTP {r.status_code} : {r.text[:300]}")
                continue
            for o in r.json().get("resultats", []):
                if o["id"] in seen:
                    continue
                seen.add(o["id"])
                offers.append({
                    "id": f"ft-{o['id']}",
                    "title": o.get("intitule", ""),
                    "company": (o.get("entreprise") or {}).get("nom", "Non précisé"),
                    "location": (o.get("lieuTravail") or {}).get("libelle", ""),
                    "contract": o.get("typeContratLibelle", "CDI"),
                    "date": o.get("dateCreation", ""),
                    "url": (o.get("origineOffre") or {}).get("urlOrigine")
                        or f"https://candidat.francetravail.fr/offres/recherche/detail/{o['id']}",
                    "description": (o.get("description") or "")[:1500],
                    "source": "France Travail",
                })
        except Exception as e:
            print(f"[FT] Erreur '{q}': {e}")
    print(f"[FT] {len(offers)} offres récupérées.")
    return offers


# ---------------------------------------------------------------- JSearch (Google Jobs)
def fetch_jsearch() -> list[dict]:
    key = os.environ.get("RAPIDAPI_KEY")
    if not key:
        print("[JSearch] Clé absente, source ignorée.")
        return []
    offers = []
    seen = set()
    date_filter = "today" if DAYS_BACK <= 1 else "3days"
    for q in SEARCH_QUERIES[:3]:  # limiter le quota gratuit
        try:
            r = requests.get(
                "https://jsearch.p.rapidapi.com/search-v2",
                headers={
                    "X-RapidAPI-Key": key,
                    "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
                },
                params={
                    "query": f"{q} CDI France",
                    "date_posted": date_filter,
                    "country": "fr",
                    "num_pages": "1",
                },
                timeout=30,
            )
            if r.status_code != 200:
                print(f"[JSearch] '{q}' -> HTTP {r.status_code}")
                continue
            payload = r.json().get("data", [])
            jobs = payload.get("jobs", []) if isinstance(payload, dict) else payload
            for o in jobs:
                oid = o.get("job_id", "")
                if oid in seen:
                    continue
                seen.add(oid)
                offers.append({
                    "id": f"js-{oid[:40]}",
                    "title": o.get("job_title", ""),
                    "company": o.get("employer_name", "Non précisé"),
                    "location": ", ".join(filter(None, [o.get("job_city"), o.get("job_country")])),
                    "contract": o.get("job_employment_type", ""),
                    "date": o.get("job_posted_at_datetime_utc", ""),
                    "url": o.get("job_apply_link", ""),
                    "description": (o.get("job_description") or "")[:1500],
                    "source": o.get("job_publisher", "Google Jobs"),
                })
        except Exception as e:
            print(f"[JSearch] Erreur '{q}': {e}")
    print(f"[JSearch] {len(offers)} offres récupérées.")
    return offers


# ---------------------------------------------------------------- main
def main():
    all_offers = fetch_france_travail() + fetch_jsearch()

    # dédoublonnage grossier (titre+entreprise)
    dedup = {}
    for o in all_offers:
        k = re.sub(r"\W+", "", (o["title"] + o["company"]).lower())[:60]
        if k not in dedup:
            dedup[k] = o
    offers = list(dedup.values())

    for o in offers:
        s, matched = score_offer(o["title"], o["description"])
        o["score"] = s
        o["matched"] = matched[:8]

    offers = [o for o in offers if o["score"] >= 5]
    offers.sort(key=lambda x: x["score"], reverse=True)

    out = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "count": len(offers),
        "offers": offers,
    }
    os.makedirs("docs", exist_ok=True)
    # conserver l'historique des 7 derniers jours
    hist_path = "docs/history.json"
    history = {}
    if os.path.exists(hist_path):
        try:
            history = json.load(open(hist_path, encoding="utf-8"))
        except Exception:
            history = {}
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    history[today] = len(offers)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    history = {d: c for d, c in history.items() if d >= cutoff}
    json.dump(history, open(hist_path, "w", encoding="utf-8"))

    with open("docs/data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"OK: {len(offers)} offres écrites dans docs/data.json")


if __name__ == "__main__":
    sys.exit(main())
