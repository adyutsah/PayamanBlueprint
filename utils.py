# 💰 Payaman Blueprint

A multi-user, multi-page personal wealth tracking and projection dashboard
built with Streamlit. Users register/log in, set a financial profile, log
transactions, and see a 15-year wealth projection with target-goal tracking.

---

## 1. Run it locally

```bash
pip install -r requirements.txt
streamlit run main.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`). Register an
account, then log in — `data/users.csv`, `data/{email}_finances.csv`, and
`data/{email}_ledger.csv` will be created automatically on first use.

---

## 2. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit: Payaman Blueprint"
git branch -M main
git remote add origin https://github.com/<your-username>/payaman-blueprint.git
git push -u origin main
```

The included `.gitignore` already excludes `data/*.csv` — **your account
credentials and financial data are never pushed to GitHub.** Only
`data/.gitkeep` (an empty placeholder so the folder exists) is committed.

---

## 3. Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with
   GitHub.
2. Click **New app**, select your `payaman-blueprint` repo and `main`
   branch.
3. Set **Main file path** to `main.py`.
4. Click **Deploy**.

No secrets or environment variables are required — the app has no external
API dependencies.

---

## ⚠️ 4. Data Persistence — read this before relying on it

This app uses **local CSV files** as its database, per the original spec.
That's simple and fully portable, but it comes with one important caveat
once deployed to Streamlit Community Cloud:

- Community Cloud containers do **not guarantee persistent disk storage**.
  Every time you `git push` a change (triggering a redeploy), or whenever
  the platform reboots/reprovisions your app's container, **any CSV files
  written at runtime (`data/*.csv`) are wiped** and the app starts fresh
  with an empty `users.csv`.
- Within a single running session (no redeploys, no reboots), data persists
  normally — it just isn't durable across deploys the way a real database
  would be.

**This is fine for:** a personal demo, a portfolio piece, or a tool you
run mostly locally and only occasionally show off via a public link.

**This is not fine for:** trusting it as your actual long-term financial
record-keeping system once it's live on Community Cloud.

If you want durable storage on Community Cloud later, the lowest-effort
upgrade path is swapping the CSV read/write calls in `utils.py` for one of:
- **Google Sheets** via `st.connection` + `gspread` (free, no server to run)
- **Supabase** (free-tier Postgres with a REST API)
- Any hosted **SQLite/Postgres** with Streamlit's `st.connection` API

Because all CSV I/O is centralized in `utils.py`, that swap only touches
one file — the four page scripts (`main.py`, `views/*.py`) wouldn't need
to change.

---

## Project structure

```
payaman_blueprint/
├── main.py              # Auth portal, global CSS, sidebar + navigation
├── utils.py              # All CSV I/O, password hashing, filename logic
├── requirements.txt
├── .gitignore
├── data/
│   └── .gitkeep          # Keeps the folder in git; CSVs are gitignored
└── views/
    ├── overview.py        # Executive Dashboard
    ├── expenses.py         # Transaction Ledger
    └── setup.py             # Financial Profile
```
