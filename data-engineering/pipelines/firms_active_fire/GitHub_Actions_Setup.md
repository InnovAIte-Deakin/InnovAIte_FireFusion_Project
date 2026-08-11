# FireFusion — Automating the FIRMS Pipeline with GitHub Actions

This turns your manual "run it in Jupyter" pipeline into one that runs **automatically every day** without you touching it — closing Gap 8 (Live Automation) from Sprint 1.

## What changed
`extract_firms.py` now reads its database credentials and FIRMS key from **environment variables first**, falling back to your real values only if those variables aren't set. This means:
- In Jupyter, on your own computer: works exactly as before, no changes needed.
- In GitHub Actions: credentials come from **GitHub Secrets** instead of being stored in the code — so your Supabase password is never visible in the repo.

## One-time setup (10 minutes)

### 1. Push these files to a GitHub repo
```
your-repo/
├── extract_firms.py
├── schema.sql
├── requirements.txt
└── .github/
    └── workflows/
        └── firms_pipeline.yml
```

### 2. Add your secrets to GitHub
In your repo: **Settings → Secrets and variables → Actions → New repository secret**

Add each of these one at a time:

| Secret name | Value |
|---|---|
| `FIRMS_MAP_KEY` | your NASA FIRMS key |
| `SUPABASE_HOST` | `aws-1-ap-south-1.pooler.supabase.com` |
| `SUPABASE_DB` | `postgres` |
| `SUPABASE_USER` | `postgres.zbgxliqmanojoknnetec` |
| `SUPABASE_PASSWORD` | your Supabase database password |
| `SUPABASE_PORT` | `5432` |

**Never commit these values directly into the code or push them to a public repo.** Secrets stay encrypted on GitHub's side and are only injected at runtime.

### 3. That's it — it will now run automatically
The workflow (`firms_pipeline.yml`) is scheduled to run **once a day at 22:00 UTC** (≈8am Victoria time). You can change the schedule by editing this line in the workflow file:
```yaml
- cron: "0 22 * * *"
```
([crontab.guru](https://crontab.guru) is useful for adjusting this.)

## Running it manually (without waiting for the schedule)
Go to your repo → **Actions tab** → select "FireFusion - FIRMS Active Fire Pipeline" → click **Run workflow**. Useful for testing or for the Sprint Review demo.

## Checking if it worked
Two places to check after any run:
1. **GitHub Actions tab** — green check = success, red X = failed. Click into the run to see the full log.
2. **Supabase → `pipeline_run_log` table** — every run (scheduled or manual) adds a row here with `status`, rows inserted, and which satellites succeeded. This is the same table we tested manually earlier.

If a run fails, the workflow also saves the log file (`firms_pipeline.log`) as a downloadable "artifact" on that run's GitHub Actions page — even on failure — so you can see exactly what went wrong without re-running it.

## Handing this pattern to Person 2 (historical pipeline)
Same setup works for the historical GeoScience Australia/CFA pipeline — just duplicate `firms_pipeline.yml` as a second workflow file (e.g. `historical_pipeline.yml`) pointing at their script, reusing the same Supabase secrets (no need to create new ones).
