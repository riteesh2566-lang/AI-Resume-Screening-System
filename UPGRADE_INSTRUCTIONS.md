# Replacing your current ResumeAI project

1. Make a backup copy of your current `resume_ai` folder.
2. Extract `ResumeAI_Upgraded.zip` into a new folder first and review the files.
3. Copy the upgraded project files over your existing project. Keep your `.git` directory so your existing Git remote/history remain connected.
4. Do **not** copy your old personal resume, `database/resume_ai.db`, or old files from `uploads/` into Git. The new `.gitignore` excludes these paths.
5. In PowerShell, from the project root:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   Copy-Item .env.example .env
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

6. Put the generated value into `SECRET_KEY` in `.env`. Configure a private recruiter email and strong password in the `BOOTSTRAP_RECRUITER_*` variables. Never commit `.env`.
7. Run `python app.py`. The app initializes its SQLite schema automatically.
8. Test candidate registration, login, resume upload, matching and logout. Test recruiter login after setting bootstrap credentials.
9. Optional semantic AI matching: `pip install -r requirements-ai.txt`, set `USE_SEMANTIC_MODEL=true` in `.env`, then restart. The first run downloads the embedding model.
10. Before committing, run `git status` and verify that `.env`, database files, and uploads are not staged.

## Git upload after testing

```powershell
git add .
git status
git commit -m "Upgrade ResumeAI security and hybrid AI matching"
git push origin main
```

Do not use `git add -f` for `.env`, database files, or uploaded resumes.
