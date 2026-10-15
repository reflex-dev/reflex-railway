# Publishing the Railway template

Steps for maintainers to create and publish this repository as a Railway template. Railway's guides: [Create a template](https://docs.railway.com/templates/create), [Best practices](https://docs.railway.com/templates/best-practices), [Publish and share](https://docs.railway.com/templates/publish-and-share).

Railway no longer reads `railway.json`/`railway.toml` for new services, so every setting below goes in the template composer. `.railway/railway.ts` records the same settings as code.

## 1. Create the template

Open **Workspace settings → Templates → New Template** and add three services. Use exactly these names (capital case, no dashes), because the reference variables depend on them.

### Postgres

- Add **Database → PostgreSQL**. It includes a volume and generated credentials.

### Redis

- Add **Database → Redis**. It includes a volume and a generated password.

### Reflex

- **Source:** GitHub repo `https://github.com/reflex-dev/reflex-railway` (builds from `Dockerfile`)
- **Settings**
  - Pre-deploy command: `alembic upgrade head`
  - Healthcheck path: `/_health`
  - Public networking: **HTTP**, target port `8080` (generate a Railway domain)
  - Icon: Reflex logo (1:1, transparent background)
- **Variables**

| Name | Value | Description |
|------|-------|-------------|
| `PORT` | `8080` | Public port the app serves on. |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | Private Postgres connection string used by the app and migrations. |
| `REFLEX_REDIS_URL` | `${{Redis.REDIS_URL}}` | Private Redis connection that stores session state shared by all workers and replicas. |
| `GRANIAN_WORKERS` | `2` | Backend worker processes per replica. Raise for larger instances. |

Click **Create Template**.

## 2. Test the template before publishing

Deploy the template URL into a fresh project and check:

- [ ] All three services deploy. The pre-deploy log shows `Running upgrade  -> 3251b24f542b, create entry table`.
- [ ] The deploy log shows no "Compiling" or "Creating Production Build" step at startup.
- [ ] `https://<domain>/_health` returns `{"status":true,"db":true,"redis":true}`.
- [ ] The guestbook loads. Sign it, reload the page, and the entry is still there.
- [ ] Redeploy. Existing browser tabs reconnect and keep working.
- [ ] Set replicas to 2, sign from two browsers, and both see each other's entries after a reload.

## 3. Publish

Go to **Workspace settings → Templates → Publish**:

- **Name:** `Reflex`
- **Category:** Starters (or Other)
- **Overview:** paste `README.md` from the first line down to (not including) "#### Build your own app". It follows Railway's required headings.
- **Demo project:** optional; link the project from step 2.
- Publish from the official Reflex workspace (`Reflex`) so the template shows the right author.

Then replace `REPLACE_WITH_TEMPLATE_CODE` in `README.md` with the template code from the template URL.
