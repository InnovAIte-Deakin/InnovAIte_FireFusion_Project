# Postman demo — FireFusion Auth0 integration

A ready-to-import Postman collection that exercises every part of the
FireFusionAPI Auth0 integration end-to-end. Use this for the demo recording
or as a quick local sanity check.

---

## What's in here

`firefusion-auth.postman_collection.json` — four requests:

| # | Request | Auth | Expected |
|---|---|---|---|
| 1 | `GET /hello/` | none | 200 + "Hello, World!" |
| 2 | `GET /hello/me` | none | 401 (proves auth is enforced) |
| 3 | `GET /hello/me` | bearer (collection OAuth) | 200 + decoded JWT claims |
| 4 | `GET /hello/admin` | bearer (collection OAuth) | 200 if admin user, 403 otherwise |

The collection also has **OAuth 2.0 + PKCE** configured at the collection
level, so you can do a real interactive Auth0 Universal Login from inside
Postman without writing any frontend code.

---

## Prerequisites

1. Postman installed (https://www.postman.com/downloads/).
2. RabbitMQ + Redis running locally:
   ```bash
   cd ../..   # to backend/
   docker compose --profile firefusion up -d broker cache
   ```
3. FireFusionAPI running locally:
   ```bash
   cd backend/firefusion-api
   source ../../venv/bin/activate
   fastapi dev app/main.py
   ```
   (Should be on http://localhost:8000.)
4. Auth0 set up per [`AUTH_SETUP.md`](../AUTH_SETUP.md), with at least
   one user assigned the `admin` role.

---

## One-time Auth0 dashboard setup for Postman

For Postman's OAuth flow to work, Auth0 needs to allow Postman's standard
callback URL. **One-off, two minutes:**

1. Auth0 dashboard → **Applications → Applications → Firefusion → Settings**.
2. Scroll to **Allowed Callback URLs**. Add (comma-separated with the
   existing localhost URL):

   ```
   https://oauth.pstmn.io/v1/callback
   ```

3. Click **Save Changes** at the bottom.

That's the URL Postman uses to receive the auth code after Auth0 redirects.

---

## Importing the collection

1. Open Postman.
2. Click **Import** (top-left).
3. Drop in `firefusion-auth.postman_collection.json` (or paste its contents).
4. The collection appears as **FireFusion Auth0 Demo** in the left sidebar.

The four collection variables (`base_url`, `auth0_domain`, `auth0_audience`,
`client_id`) are pre-populated with the values from this branch. If you're
on a different tenant, update them: click the collection → **Variables**
tab → edit the **Current Value** column.

---

## Getting a token (interactive user login)

This is the magic bit — proves the full flow without a frontend.

1. Click on the **FireFusion Auth0 Demo** collection name in the sidebar.
2. Open the **Authorization** tab (it'll show OAuth 2.0 already configured).
3. Scroll to the bottom and click **Get New Access Token**.
4. A browser window pops up showing **Auth0 Universal Login**.
5. Log in as your test user (e.g. the one with the `admin` role).
6. After login, the browser shows "Authentication complete" and Postman
   captures the token automatically.
7. Click **Use Token** in the Postman dialog.

Postman now has a fresh access token cached for the collection. All requests
under it inherit this token automatically.

> **Tip:** to get a token from a *different* user (e.g. a non-admin to
> demonstrate the 403 case), click **Get New Access Token** again. Postman
> will go through the login flow again. If your browser still has the
> previous Auth0 session, you may need to log out at
> `https://YOUR_TENANT.au.auth0.com/v2/logout` first.

---

## Running the demo

Click each request top-to-bottom:

1. **Public** → 200, "Hello, World!". The server is alive.
2. **No token** → 401, missing-header error. Authentication is enforced.
3. **With token** → 200 + decoded claims. JWKS verification, RS256 check,
   audience check, issuer check, expiry check all silently pass.
4. **Admin route**:
   - If your user has the `admin` role → 200 + "Hello, admin!".
   - If not → 403 + "Role 'admin' required".

Each request also has automated tests written into Postman that assert the
expected status code and response shape — the green **Tests** indicator at
the bottom of the response panel confirms they passed.

---

## What this proves end-to-end

- **Auth0 issued a real user token** via OAuth 2.0 Authorization Code with
  PKCE — the same flow the React frontend will use later.
- **The Post-Login Action ran** during the login (because this was an
  interactive login, not a Machine-to-Machine grant). The user's roles got
  copied into the token's custom claim `https://firefusion.com/roles`.
- **FireFusionAPI verified the token** correctly: signature, issuer,
  audience, expiry — all checked.
- **Role-based access control works** — the API allowed the admin user
  through to `/hello/admin` and would have blocked any non-admin user with
  a 403.

---

## Recording the demo video

Suggested script (~3 minutes):

1. **Show Auth0 dashboard briefly** — the API, the SPA, the role, the
   Post-Login Action. (~30 seconds)
2. **Show the API code** — `app/auth/jwt_validator.py`,
   `app/dependencies.py`, `app/routers/hello.py`. Skim, don't read.
   (~30 seconds)
3. **Show the API running** — terminal with `fastapi dev` output.
   (~5 seconds)
4. **Open Postman, click Get New Access Token** — browser pops up,
   Universal Login appears, log in as your admin user. (~30 seconds)
5. **Run requests 1–4 in order** — narrate the expected status codes.
   Show the green Tests indicator passing each time. (~60 seconds)
6. **(Optional) decode the token at jwt.io** — show the role claim
   `https://firefusion.com/roles: ["admin"]` is actually present. (~30
   seconds)

Total ~3 minutes, covers the full story.

---

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| "callback URL mismatch" in Auth0 login | Postman's callback `https://oauth.pstmn.io/v1/callback` not added to Allowed Callback URLs. See "One-time Auth0 dashboard setup" above. |
| Postman never captures the token | Browser blocked Postman's redirect. Try Postman's desktop app instead of the web version. |
| All requests return "Service unavailable" | API isn't running. `fastapi dev app/main.py` from `backend/firefusion-api/`. |
| Request 3 returns 401 instead of 200 | Token expired (default Auth0 token lifetime is 24h). Click **Get New Access Token** again. |
| Request 4 returns 403 even though you logged in as admin | (a) Test user wasn't actually assigned the `admin` role; (b) Post-Login Action isn't deployed or attached to the post-login trigger; (c) `AUTH0_ROLE_NAMESPACE` in your `.env` doesn't match the namespace in the Action. |
