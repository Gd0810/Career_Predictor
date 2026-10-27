# NextGen Career Predictor

A Django project with three logins — **Admin**, **Company**, and **Candidate** — matching the
spec: single register page (student/company toggle forms), single login form for both roles,
company job/quiz posting with an anti-cheat test window, candidate AI-powered profile/roadmap/
resume tools, and a custom admin analytics dashboard.

## 1. Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # then edit .env (see below)

python manage.py migrate
python manage.py train_ml_models   # trains the Salary & Placement ML models (also auto-trains on first use)
python manage.py createsuperuser   # this becomes your ADMIN login
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` — it redirects to the login page.
- **Admin** → log in with the superuser email/password you just created → custom admin dashboard
  (not Django's default `/admin/` UI, though that's still available at `/django-admin/` for raw CRUD).
- **Company** → register via the "Company" tab on the register page.
- **Candidate** → register via the "Student" tab on the register page.

## 2. NVIDIA AI Build integration (`.env`)

The spec asks for 4 NVIDIA AI Build (https://build.nvidia.com/models) accounts, one per AI
feature. Fill these into `.env`:

```
NVIDIA_API_KEY_RESUME_PARSER=...
NVIDIA_API_KEY_CAREER_ROADMAP=...
NVIDIA_API_KEY_RESUME_ANALYZER=...
NVIDIA_API_KEY_CHAT=...
```

Each key is used independently by `candidateapp/utils/ai_client.py`, which calls the
OpenAI-compatible `/chat/completions` endpoint NVIDIA AI Build exposes. **If a key is left
blank (or the call fails for any reason), every AI feature automatically falls back to a
deterministic rule-based result** (regex resume parsing, skill-overlap career matching, etc.)
so the whole app stays fully functional even before you add keys — this was verified end-to-end.

Where each key is used:
| Feature | Module | Fallback if no key |
|---|---|---|
| Resume → profile auto-fill | `candidateapp/utils/resume_parser.py` | regex/keyword extraction |
| Resume quality analysis | `candidateapp/utils/resume_analyzer.py` | rule-based scoring |
| Career recommendation + skill roadmap | `candidateapp/utils/roadmap.py` | skill-overlap matching against `career_data.py` |
| (Reserved) chat/assistant key | `NVIDIA_API_KEY_CHAT` | not wired to a UI in this build — see note below |

## 3. Salary Prediction & Placement Probability (real ML, no API needed)

`candidateapp/utils/ml_models.py` trains real `scikit-learn` `RandomForestRegressor` /
`RandomForestClassifier` models on a synthetic-but-realistic dataset generated with a fixed
seed (no external dataset required). Run `python manage.py train_ml_models` any time to
retrain; models are cached to `candidateapp/ml_artifacts/*.joblib` and auto-train on first use
if missing.

## 4. External Jobs (LinkedIn / Indeed / Naukri) & Courses (YouTube / Udemy)

**Important honesty note:** LinkedIn, Indeed and Naukri actively block scraping and doing so
violates their Terms of Service — a scraper built today would also break quickly as they change
their markup. Instead, `candidateapp/utils/external_links.py` generates **pre-filled, clickable
search-result deep links** to those sites based on the candidate's role and missing skills
(exactly what a human typing the search themselves would land on). This is legitimate, needs no
API key, and is the standard approach real job-aggregator apps use without a paid data license.
If you later get access to a paid API (LinkedIn Talent API, Naukri partner API, a YouTube Data
API key, etc.), swap the URL builders in that file for real API calls — the rest of the app
doesn't need to change.

## 5. Job-Quiz anti-cheat behaviour

`static/js/quiz_anticheat.js` + `templates/candidate/quiz.html` implement:
- Detects tab switch / window blur / Alt+Tab attempts, each counted as a violation with an alert.
- After **3 violations** (`MAX_QUIZ_VIOLATIONS` in `settings.py`), the quiz auto-submits.
- Countdown timer based on the quiz's `quiz_timing_minutes`; auto-submits on expiry too.
- Right-click / context menu disabled during the test.
- Note: browsers cannot fully prevent a user from opening a new tab (no JS API grants that level
  of OS control) — this implementation detects the *attempt* (blur/visibility change) reliably,
  which is the standard approach proctoring tools use in a plain browser without a lockdown
  browser plugin.

## 6. Switching to MySQL

By default the project uses SQLite (zero config, fully runnable). To use MySQL instead:
1. `pip install mysqlclient`
2. In `.env`, set `USE_MYSQL=True` and fill in `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.
3. Create the database in MySQL, then `python manage.py migrate`.

## 7. Project structure

```
accounts/        # Custom User model (email login, role field), register/login views
companyapp/       # CompanyProfile, JobQuiz, Job, JobApplication, QuizAttempt + views
candidateapp/     # CandidateProfile, Skill, Project, resume/roadmap/ML AI features
adminapp/         # Custom admin dashboard (uses superuser creds, not Django's default UI)
templates/        # All HTML templates, grouped by app
static/           # CSS + quiz anti-cheat JS
```

## 8. What's stubbed vs. fully implemented

- ✅ Fully implemented & tested: auth/roles, registration toggle, job posting, quiz JSON upload
  + anti-cheat + auto-scoring, application review/status workflow, candidate profile/skills/
  projects, resume upload + AI-or-fallback parsing, resume analyzer + progress tracker, career
  recommendation + skill roadmap (AI-or-fallback), match-score calculation, salary prediction
  and placement probability (real ML), external job/course link generation, custom admin
  dashboard with analytics + CRUD toggle/delete.
- ⚠️ `NVIDIA_API_KEY_CHAT` is wired into `ai_client.py` and ready to use, but no chat-widget UI
  was built in this pass — add a small view + template calling
  `call_nvidia_ai("chat", system_prompt, user_message, json_mode=False)` if you want a chatbot.
- ⚠️ Only PDF/TXT resume text extraction is implemented (via `pdfplumber`); DOCX resumes aren't
  parsed — add `python-docx` and extend `resume_parser.py` if needed.
