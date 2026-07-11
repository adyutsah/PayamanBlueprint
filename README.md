# ----------------------------------------------------------------------------
# Payaman Blueprint — .gitignore
# ----------------------------------------------------------------------------

# App data — user credentials (hashed) and personal financial data.
# NEVER commit real user CSVs to a public GitHub repo.
data/*.csv
!data/.gitkeep

# Streamlit secrets (if you later add API keys / DB connection strings)
.streamlit/secrets.toml

# Python
__pycache__/
*.pyc
*.pyo
.Python
*.egg-info/

# Virtual environments
venv/
.venv/
env/

# Editors / OS
.DS_Store
.vscode/
.idea/
