# Django Project Setup Guide

This guide provides step-by-step instructions on how to set up, run, and manage this Django project.

## Initial Setup

### 1. Clone the Repository

```bash
git clone [repository-url]
cd [repository-directory]
```

### 2. Active vertual environment

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Migration and Run Server

```bash
python manage.py runserver
python manage.py makemigrations
python manage.py migrate
```
### 5. Create Super User

```bash
python manage.py createsuperuser
```
### 6. Dump and Load Data

```bash
python manage.py dumpdata > database_dump.json
python manage.py loaddata database_dump.json
