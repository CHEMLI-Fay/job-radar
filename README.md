# Job Radar

A small dashboard for tracking recent junior data science and AI job listings. It collects offers from France Travail and JSearch, applies a transparent keyword score, and writes JSON files used by the web page.

## How it works

```text
France Travail + JSearch -> fetch_jobs.py -> scoring and deduplication
                                      -> docs/data.json -> docs/index.html
                                      -> docs/history.json
```

- `fetch_jobs.py` fetches offers and ranks them using editable keywords.
- `docs/index.html` displays the latest generated data.
- `.github/workflows/daily.yml` runs the collection workflow at 05:00 UTC and can also be started manually.

The schedule is in UTC, so the local time in France changes with daylight saving time. Job availability and API responses depend on the data providers.

## Run locally

Use Python 3.12 or newer. From the repository root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Set the credentials in your local shell before fetching offers.
$env:FT_CLIENT_ID = "your-client-id"
$env:FT_CLIENT_SECRET = "your-client-secret"
$env:RAPIDAPI_KEY = "your-rapidapi-key"

.\.venv\Scripts\python.exe fetch_jobs.py
.\.venv\Scripts\python.exe -m http.server 8000 --directory docs
```

Open <http://localhost:8000>. If a provider's credentials are absent, the script skips that source. Never commit API keys.

## GitHub Actions and Pages

Add `FT_CLIENT_ID`, `FT_CLIENT_SECRET`, and `RAPIDAPI_KEY` as repository Actions secrets. Run the workflow manually once from the **Actions** tab, then check `docs/data.json`. To publish the dashboard, configure GitHub Pages to serve the `docs/` folder from `main`.

## Customize

Change `SEARCH_QUERIES`, `SKILL_KEYWORDS`, and `DAYS_BACK` in `fetch_jobs.py`. The score is a simple keyword heuristic; verify each listing on the original job site before relying on it.
