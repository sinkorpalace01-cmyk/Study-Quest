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

## Deploying

Set all `.env.example` variables as Vercel project environment variables. Set `DEBUG=0`, `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` for the deployment hostname, and use a fresh `DJANGO_SECRET_KEY` before first deployment. Run migrations against the TiDB database. Vercel automatically detects `manage.py` as Django and handles static assets. Vercel filesystem is ephemeral, so uploads should continue to use Cloudinary. `.vercelignore` excludes local credentials and development files.

The old browser-only prototype is retained under `prototype/` for reference; it is not the Django application.
