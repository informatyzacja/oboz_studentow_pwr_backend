# WrocTech Students' Camp App Backend - Django Project (Obóz Studentów PWr)

This project is a Django backend for an application that manages camps for students of Wrocław University of Science and Technology. The project includes a Django backend and a Vue.js frontend.

## Project Structure

- `manage.py` - The main tool for managing the Django project.
- `requirements.txt` - A list of Python dependencies.
- `obozstudentow/` - The main Django application.
- `obozstudentow_async/` - Asynchronous modules.
- `obozstudentowProject/` - Django project configuration.
- `static/` - Static frontend files.
- `templates/` - HTML templates.

## Requirements

- Python 3.8+

## Installation

1. Clone the repository:
```bash
git clone <REPO_URL>
cd oboz_studentow_pwr_backend
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install pre-commit hooks to ensure code quality:
```bash
pre-commit install
```

3. Create a `.env` file in the project's root directory and add the following environment variables:
```bash
ALLOWED_HOSTS='*'
CORS_ALLOW_ALL_ORIGINS=True
SECRET_KEY="secret_key_(change_this)"
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

4. Apply migrations:
```bash
python manage.py migrate
```

5. Create a superuser account:
```bash
python manage.py createsuperuser
```
and follow the instructions.


## Running
Run the development server:
```bash
python manage.py runserver
```

The development server will be available at `http://localhost:8000`. By navigating to `http://localhost:8000/admin/`, you can log in to the admin panel.