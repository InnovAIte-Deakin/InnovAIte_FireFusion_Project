# Auth0 Setup — FireFusionAPI

Step-by-step runbook for configuring Auth0 to work with this service. Follow
top-to-bottom. Estimated time: 20–30 minutes the first time.

When you finish, you'll have three values to paste into your local `.env`:

- `AUTH0_DOMAIN`
- `AUTH0_AUDIENCE`
- `AUTH0_ROLE_NAMESPACE`

…and an Auth0 tenant configured with an API resource, an SPA Application,
roles, and a Post-Login Action that copies role data into JWTs.

---

## 1. Sign up and create the tenant

1. Open <https://auth0.com/signup>.
2. Sign up with whatever email is convenient — a personal email is fine for
   the capstone. You can add a project/team email as a co-admin later via
   **Settings → Tenant Members → Add Tenant Access**, which gives the team
   account equivalent access without any data loss.
3. When asked **"What kind of application are you working on?"** → pick
   **Single Page Web Applications**.
4. **"What technology are you using?"** → **React**.
5. **"What's your role?"** → whatever fits (Developer / Student).
6. **Tenant Domain.** Suggested: `firefusion-dev`. Full domain becomes
   `firefusion-dev.au.auth0.com`. **Pick the AU (Australia) region** for
   lower latency and in-region data residency.
7. Accept the terms and click **Create Account**.

You should land on the Auth0 dashboard. The tenant domain is shown top-left.

> **Save this:** `AUTH0_DOMAIN=firefusion-dev.au.auth0.com` (or whatever
> you chose).

---

## 2. Create the API resource

This is what FireFusionAPI is, *as far as Auth0 is concerned*. Tokens will
carry this identifier in their `aud` claim.

1. In the dashboard sidebar: **Applications → APIs → + Create API**.
2. Fill in:
   - **Name:** `FireFusionAPI`
   - **Identifier:** `https://api.firefusion.com`
     - This is the `aud` value. It does **not** have to be a real URL — it
       just has to be unique inside this tenant. Once set, **it cannot be
       changed**.
   - **JSON Web Token Profile:** Auth0 (default)
   - **JSON Web Token Signing Algorithm:** **RS256**
   - **Access Policy for Applications:** leave both **Per-app authorization** (default)
3. Click **Create**.
4. On the new API's page, open the **Settings** tab and scroll to **RBAC
   Settings**. Toggle on:
   - ✅ **Enable RBAC**
   - ✅ **Add Permissions in the Access Token**
5. Click **Save**.

> **Save this:** `AUTH0_AUDIENCE=https://api.firefusion.com`

### Authorize your SPA application

Because the access policy is "Per-app authorization", your React app needs to
be explicitly granted access:

1. On the same API's page, click the **Application Access** tab.
2. Find your SPA Application (the one named e.g. `Firefusion`) and click **Edit**.
3. Enable **User-delegated Access**, save.

Without this, the React app gets *"Service not found: https://api.firefusion.com"* on login.

---

## 3. Create the SPA Application

This represents the React frontend that will request tokens. (Auth0 may have
auto-created a "Default App" during signup — feel free to use it, or create a
new one as below.)

1. **Applications → Applications → + Create Application**.
2. **Name:** `Firefusion`. **Type:** Single Page Web Applications.
3. Click **Create**.
4. On the new app's **Settings** tab, scroll to **Application URIs** and set:
   - **Allowed Callback URLs:** `http://localhost:5173`
     - Vite's default dev port. If you change Vite's port, update this.
   - **Allowed Logout URLs:** `http://localhost:5173`
   - **Allowed Web Origins:** `http://localhost:5173`
5. Click **Save Changes** at the bottom.
6. Stay on this page — you'll need the **Domain** and **Client ID** values
   for the React app's environment variables later. (They aren't needed by
   FireFusionAPI itself, only by the frontend.)

---

## 4. Create roles

The TL specifically called out role-based access. Define the roles up front.

1. **User Management → Roles → + Create Role**.
2. Create `admin`. (You can give it a description like "Full administrative
   access" but it's optional.)
3. Repeat for `user`.

---

## 5. Create at least one test user and assign a role

1. **User Management → Users → + Create User**.
2. Email: yourself@example.com (or use a real address — Auth0 will let you
   sign in with it). Pick a password.
3. **Connection:** `Username-Password-Authentication`.
4. Click **Create**.
5. On the new user's page, open the **Roles** tab → **Assign Roles** →
   pick `admin` → **Assign**.

This is the user you'll log in as during the demo recording.

---

## 6. Create the Post-Login Action that injects roles into JWTs

This is the most important step — without it, your tokens won't carry role
information and `/hello/admin` will always return 403.

1. **Actions → Library → Create Action → Build Custom**.
2. **Name:** `Add roles to access token`. **Trigger:** `Login / Post Login`.
   **Runtime:** Node 22 (recommended). Click **Create**.
3. Replace the editor contents with:

   ```javascript
   exports.onExecutePostLogin = async (event, api) => {
     const namespace = "https://firefusion.com/";
     const roles = event.authorization?.roles ?? [];
     api.accessToken.setCustomClaim(`${namespace}roles`, roles);
   };
   ```

4. Click **Save Draft**, then **Deploy**.
5. Go to **Actions → Triggers → post-login**.
6. From the right-hand panel ("Custom"), drag **Add roles to access token**
   into the flow between the **Start** and **Complete** circles.
7. Click **Apply**.

> **Save this:** `AUTH0_ROLE_NAMESPACE=https://firefusion.com/`

---

## 7. Fill in your local `.env`

From `backend/firefusion-api/`:

```bash
cp .env.example .env
```

Then edit `.env` to match:

```bash
# Existing infrastructure (defaults match docker-compose)
BROKER_URL=amqp://guest:guest@localhost:5672
CACHE_URL=redis://localhost:6379

# Auth0
AUTH0_DOMAIN=firefusion-dev.au.auth0.com
AUTH0_AUDIENCE=https://api.firefusion.com
AUTH0_ROLE_NAMESPACE=https://firefusion.com/
```

---

## 8. Bring up local infrastructure

The API can't start without RabbitMQ (broker) and Redis (cache) running.
Use the project's docker-compose:

```bash
cd ../  # to backend/
docker compose --profile firefusion up -d broker cache
```

This starts only the two dependencies, not the API itself (we'll run it
locally with `fastapi dev` so changes hot-reload).

---

## 9. Run and verify

```bash
cd firefusion-api
pip install -r requirements.txt
fastapi dev app/main.py
```

In another terminal:

```bash
# Public — should always return 200
curl -i http://localhost:8000/hello/

# Get a test token from the dashboard:
#   Applications → APIs → FireFusionAPI → Test → Copy Token
TOKEN="paste-here"

# Authenticated — should be 401 without, 200 with
curl -i http://localhost:8000/hello/me
curl -i -H "Authorization: Bearer $TOKEN" http://localhost:8000/hello/me

# Admin — 403 with the dashboard test token (no role claim)
# To get a 200, log in as your admin user via the React frontend
curl -i -H "Authorization: Bearer $TOKEN" http://localhost:8000/hello/admin
```

If `/hello/me` returns 200 with a token and 401 without, the JWKS fetch,
RS256 verification, audience check, issuer check, and expiry check are all
working. That's the core deliverable.

To verify role-based access for the demo, you'll need a token issued through
an interactive login (not the dashboard "Test" button), because Actions only
run on real logins. The React frontend is what does this in practice.

---

## Common problems and what they mean

| Symptom | Likely cause |
|---|---|
| `pydantic_core._pydantic_core.ValidationError` on startup | A required env var is missing in `.env`. Check spelling. |
| `aiormq.exceptions.AMQPConnectionError` on startup | RabbitMQ isn't running. Did you `docker compose up broker cache`? |
| `401 — Token signature invalid` | `AUTH0_DOMAIN` is wrong, or token came from a different tenant. |
| `401 — Token claims invalid: Invalid audience` | `AUTH0_AUDIENCE` doesn't match the API identifier. |
| `403 — Role 'admin' required` even with admin user | Post-Login Action not deployed, not added to the trigger flow, or the namespace doesn't match `AUTH0_ROLE_NAMESPACE`. Or you used the dashboard "Test" token (which bypasses the Action). |
| Server starts but every protected route 401s | Check that you're sending `Authorization: Bearer <token>` (not just the raw token, and not lowercased). |

---

## Reference links

- Auth0 React quickstart: https://auth0.com/docs/quickstart/spa/react/interactive
- Auth0 Backend (Python) quickstart: https://auth0.com/docs/quickstart/backend/python
- Authorization Code with PKCE flow: https://auth0.com/docs/get-started/authentication-and-authorization-flow/authorization-code-flow-with-proof-key-for-code-exchange-pkce
- JSON Web Key Sets explained: https://auth0.com/blog/navigating-rs256-and-jwks/
- python-jose docs: https://python-jose.readthedocs.io/
- jwt.io (paste any token to decode): https://jwt.io
