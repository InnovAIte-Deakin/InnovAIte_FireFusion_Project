# Supabase setup (before PR)

Use this checklist once per machine. **Do not commit `.env` or database passwords.**

## 1. Get credentials from Supabase Dashboard

| What you need | Where in Supabase |
|---------------|-------------------|
| **API URL** | Project Settings → API → **Project URL** |
| **API key** | Project Settings → API → **service_role** key (for pipeline load) |
| **DB password** | Project Settings → Database → reset/view password (for SQL Editor / psql only) |

### Map to `.env` (Python pipeline)

The CFA scripts use the **REST API**, not the `postgresql://` string directly:

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=<paste service_role key here>
```

**Not** the `postgresql://postgres:...@db....` URL in `SUPABASE_URL`.

Optional (direct SQL / DBeaver only):

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.your-project-ref.supabase.co:5432/postgres
```

## 2. Create local `.env`

```powershell
cd "F:\Deakin Assignments\SEM 4\SIT782\InnovAIte_FireFusion_Project\data-engineering\pipelines\cfa_incident_summary"
copy .env.example .env
notepad .env
```

Fill in `SUPABASE_URL` and `SUPABASE_KEY`. Save. **Never commit `.env`.**

## 3. Run SQL migrations (Supabase SQL Editor)

Dashboard → **SQL** → New query → run in order:

1. `sql/create_cfa_district_registry.sql`
2. `sql/alter_fire_incident_record_cfa.sql`

If `fire_incident_record` or hub tables do not exist yet, run the team’s base schema first:

`backend/utilities/v2/aggregator-init.sql`  
(Only on a fresh DB — it drops existing tables.)

## 4. Prerequisites (team data)

| Table | Required before CFA load |
|-------|---------------------------|
| `location_registry` | Victoria grid loaded (non-empty) |
| `time_registry` | Minute registry for your incident years (non-empty) |

## 5. Verify connection

```powershell
pip install -r requirements.txt
python scripts/verify_supabase_setup.py
```

Expected: all four tables **OK**, `location_registry` and `time_registry` not empty.

## 6. Run pipeline

```powershell
# Place raw file: data/raw/cfa_incident_summary.xlsx
python main.py --profile
python main.py --preprocess
python main.py --validate
python main.py --load
```

Dry run (no upload):

```powershell
python main.py --load --dry-run
```

## 7. Security

- Do not paste **service_role** keys or DB passwords in GitHub, Discord, or chat.
- Use **service_role** only locally / in secure CI — it bypasses Row Level Security.
- For the PR, only commit `.env.example` (placeholders), never `.env`.

## Troubleshooting

| Error | Fix |
|-------|-----|
| `Invalid API key` | Wrong key or used anon key without table permissions — use **service_role** for load |
| `relation "cfa_district_registry" does not exist` | Run step 3 SQL migrations |
| `location_registry is empty` | Run grid notebook / team grid load |
| `datetime(s) not found in time_registry` | Extend time_registry date range for your CFA file years |
| SSL / connection errors | Check VPN/firewall; confirm project is not paused in Supabase |
