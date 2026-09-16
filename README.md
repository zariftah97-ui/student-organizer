# StudyOS

A calm, local-first academic management web app built with Django and SQLite.

## Run on Windows
1. Install Python 3.11+ and make sure `python` or `py` works in Command Prompt.
2. Extract this ZIP.
3. Double-click `run.bat`.
4. Open http://127.0.0.1:8000/

The launcher creates a virtual environment, installs dependencies, runs migrations, and starts the local development server. Your data is stored in `db.sqlite3`; uploaded files are stored in `media/`.

## Features
- Accounts and isolated per-user data
- Student profile and semesters
- Courses with teacher, credit, code, and color
- Syllabus progress
- Tasks
- Assessments and marks
- Grade / GPA / CGPA calculations
- Notes
- Calendar events
- File uploads
- Global search
- JSON data export
- Sage/peach/yellow light theme and Deep Garden dark theme
- Optional StudyOS AI through `OPENAI_API_KEY`

## Important
`runserver` is intended for local development, not public production hosting. For production deployment, use a WSGI/ASGI server, HTTPS, a secret environment variable, `DEBUG=False`, appropriate `ALLOWED_HOSTS`, static/media handling, backups, and `python manage.py check --deploy`.
