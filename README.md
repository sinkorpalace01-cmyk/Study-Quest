# StudyQuest (Django)

StudyQuest is a mobile-friendly learning app that turns a topic or uploaded notes into an AI-generated, multi-level quiz. Learners earn XP and badges, build streaks, invite classmates, and receive verifiable PDF certificates with built-in sharing.

## Run locally

```powershell
uv venv .venv --python 3.12
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
Copy-Item .env.example .env
# Fill in .env with your own credentials.
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

Open http://localhost:8000/. The local `.env` is configured for the requested `hacktoberfeast` TiDB database and ignored by Git. StudyQuest tables use a `studyquest_` prefix in Django's app labels so they can coexist with the pre-existing project tables in that database. Migrations have been applied with TLS certificate and host identity verification enabled.

Use `/admin/` for the custom management area. The first platform owner login is stored in ignored `.local-admin.txt`. Any signed-in learner can invite another learner; only the platform owner can invite administrators, change account roles, and delete another user's account. Owners can update user email, password, profile, XP, streak and access, plus the app name, logo, contact details, registration setting and service credentials. Service credential overrides are encrypted in TiDB using `DJANGO_SECRET_KEY`; keep this key stable or re-enter overrides after rotating it. User and site images, and quest sources and cover art, accept a device upload or a URL. Uploads go to Cloudinary.

The home page starts with three image slides stored in `static/images/`. Staff can edit or replace them at `/admin/hero/` with text, a device image/video upload, or a direct media URL. Hero copy is length-limited so its full message and controls fit the first screen on common phone and desktop sizes. The public `/contact/` form saves messages to TiDB, emails the configured site contact, and lets staff track replies in `/admin/contact/`. Welcome, invitation, password reset, contact, and certificate mail use the current site name, logo and contact details in HTML and plain-text versions.

Quest generation first tries Google's Gemma 4 model through the Gemini API, then Groq using `openai/gpt-oss-20b`, the current supported replacement model for the retired Llama models. Groq offers this model on the free-plan limits. Provider keys, TiDB, Cloudinary and Gmail SMTP settings are read on the server from `.env`; API, media and email credentials can also be rotated in `/admin/integrations/`. A prior Groq request with the provided key returned HTTP 401, which indicates an authorization issue independent of the model; Gemma generation worked. If both AI services are unavailable, the quest form reports the error; it does not invent questions. PDF certificates are generated with ReportLab, include a verification QR code, can be downloaded, and are emailed to the learner. Learners can share achievements through the device share sheet, WhatsApp, LinkedIn, or a verification link. Set `SITE_URL` to your deployed origin for correct certificate verification links.

## Prepare for GitHub and Vercel

The Git repository root is this `App/` directory. It already has the GitHub `origin` remote and a `main` branch. `.env`, `.env.*` (except the safe `.env.example` template), `.local-admin.txt`, `.vercel/`, the SQLite database, uploaded media, and generated `staticfiles/` are ignored. Never add live credentials to source files or commit `.env`.

Review and push your changes from PowerShell:

```powershell
git status --short
git add -A
git diff --cached --check
git status --short
git commit -m "Prepare StudyQuest for deployment"
git push origin main
```

Import the GitHub repository into Vercel and leave the project root at the repository root. This repository uses Vercel Services: set the project framework to **Services** so `vercel.json` routes public requests to the Django `app` service. The legacy browser-only `prototype` is configured as an internal Node service and receives no public traffic. Django reads `config.settings.WSGI_APPLICATION` and runs `collectstatic` for the configured `STATIC_ROOT`; `.python-version` selects Python 3.12. Static files are served through Vercel's CDN. User uploads must stay on Cloudinary because Vercel's function filesystem is temporary.

In Vercel Project Settings → Environment Variables, set these for Production and, if you want preview deployments, set a separate Preview database and secrets:

| Variable | Value |
| --- | --- |
| `DJANGO_SECRET_KEY` | A newly generated, long random value used only for deployment. Keep it stable because encrypted service credentials depend on it. |
| `DEBUG` | `0` |
| `SITE_URL` | The final public HTTPS origin, such as `https://your-project.vercel.app`; use the custom domain if you add one. |
| `ALLOWED_HOSTS` | `.vercel.app,your-domain.example` (omit the example domain if unused). |
| `CSRF_TRUSTED_ORIGINS` | `https://*.vercel.app,https://your-domain.example` (omit the example domain if unused). |
| `TIDB_HOST`, `TIDB_PORT`, `TIDB_USER`, `TIDB_PASSWORD`, `TIDB_DATABASE` | Your TiDB Cloud connection values. The app verifies TLS using the installed CA bundle. |
| `GEMINI_API_KEY`, `GROQ_API_KEY` | Your server-side AI provider keys. The model variables are optional and use the defaults in `.env.example`. |
| `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` | Your Cloudinary upload credentials. |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | The sending mailbox and its SMTP app password. |

Keep these variables out of GitHub. Use a fresh Django secret key in Vercel rather than copying the local key. If you enable Preview deployments, a separate TiDB database avoids preview signups and test data mixing with production.

Before the first live deployment, connect the Vercel CLI to the project, configure its Production variables, then apply database migrations from your trusted local checkout:

```powershell
vercel link
vercel env run -e production -- .\.venv\Scripts\python.exe manage.py migrate
```

Then push `main` to trigger a deployment, or import the repository in Vercel and deploy from its dashboard. Check the generated deployment URL, then update `SITE_URL`, `ALLOWED_HOSTS`, and `CSRF_TRUSTED_ORIGINS` for your chosen hostname and redeploy if you changed them. Configure Vercel's Production branch as `main` to deploy future pushes automatically.

Vercel documents Django detection and static collection in its [Django deployment guide](https://vercel.com/docs/frameworks/full-stack/django). The Python runtime is currently marked Beta in Vercel's [Python runtime documentation](https://vercel.com/docs/functions/runtimes/python). The Hobby plan is limited to personal, non-commercial use; check Vercel's current [Hobby plan terms](https://vercel.com/docs/plans/hobby) if this platform will be used commercially.

The old browser-only prototype is retained under `prototype/` for reference; it is not the Django application.
