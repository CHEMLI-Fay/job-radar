# 🎯 Job Radar — Dashboard d'offres CDI quotidien

Dashboard qui affiche chaque matin les dernières offres CDI (Data Scientist / AI Engineer junior) matchées avec ton profil, collectées via l'API France Travail et JSearch (Google Jobs : couvre LinkedIn, Indeed, WTTJ…).

## Déploiement en 5 étapes (~20 min, une seule fois)

### 1. Obtenir la clé France Travail (gratuit)
1. Va sur https://francetravail.io → « Se connecter » → crée un compte.
2. Dans ton espace, crée une **application**, puis abonne-la à l'API **« Offres d'emploi v2 »**.
3. Note le **Client ID** et le **Client Secret**.

### 2. Obtenir la clé JSearch (gratuit)
1. Crée un compte sur https://rapidapi.com
2. Cherche **« JSearch »** (by OpenWeb Ninja) → « Subscribe to Test » → plan **Basic (gratuit)**.
3. Note ta clé **X-RapidAPI-Key**.

### 3. Créer le repo GitHub
1. Compte sur https://github.com si besoin.
2. Nouveau repo → nom : `job-radar` → **Public** (obligatoire pour Pages gratuit).
3. Upload tout le contenu de ce dossier `job-dashboard/` (y compris le dossier caché `.github/`).
   - Le plus simple : GitHub → « uploading an existing file » → glisser-déposer, ou via git :
   ```
   git init && git add . && git commit -m "init"
   git remote add origin https://github.com/TON_USER/job-radar.git
   git push -u origin main
   ```

### 4. Ajouter les secrets
Repo → **Settings → Secrets and variables → Actions → New repository secret** :
| Nom | Valeur |
|---|---|
| `FT_CLIENT_ID` | Client ID France Travail |
| `FT_CLIENT_SECRET` | Client Secret France Travail |
| `RAPIDAPI_KEY` | Clé RapidAPI |

### 5. Activer GitHub Pages
1. Repo → **Settings → Pages** → Source : `Deploy from a branch` → Branch : `main`, dossier `/docs` → Save.
2. Repo → onglet **Actions** → workflow « Mise à jour quotidienne des offres » → **Run workflow** (premier lancement manuel).

✅ Ton dashboard sera accessible à : `https://TON_USER.github.io/job-radar/`
Il se met à jour **tout seul chaque matin à 7h** (offres publiées dans les dernières 48h).

## Test en local (optionnel)
```
set FT_CLIENT_ID=... & set FT_CLIENT_SECRET=... & set RAPIDAPI_KEY=...
python fetch_jobs.py
python -m http.server 8000 --directory docs
```
Puis ouvre http://localhost:8000

## Personnalisation
- Mots-clés / scoring : modifie `SKILL_KEYWORDS` et `SEARCH_QUERIES` dans `fetch_jobs.py`.
- Fenêtre de fraîcheur : variable `DAYS_BACK` (défaut 2 jours).
- Heure de mise à jour : le `cron` dans `.github/workflows/daily.yml`.
