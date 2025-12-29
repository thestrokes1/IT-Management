# How to Run IT Management Platform Locally

## Step-by-Step Instructions

### Prerequisites
- Python 3.10+ installed on your system
- pip package manager

### Setup Steps

#### 1. Navigate to Project Directory
```bash
cd it_management_platform/backend
```

#### 2. Create Virtual Environment
```bash
python -m venv venv
```

#### 3. Activate Virtual Environment
```bash
# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate
```

#### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 5. Copy Environment Configuration
```bash
# Copy the environment template
copy .env.example .env
```

#### 6. Edit Environment File
Open `.env` file in a text editor and update with your settings:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
```

#### 7. Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

#### 8. Create Superuser Account
```bash
python manage.py createsuperuser
```
Follow the prompts to create your admin account.

#### 9. Setup Sample Data (Optional)
```bash
python setup_database.py
```

#### 10. Run Development Server
```bash
python manage.py runserver
```

### Access the Application

Once the server is running, you can access:

- **Main Web Interface**: http://127.0.0.1:8000/
- **Admin Interface**: http://127.0.0.1:8000/admin/
- **API Documentation**: http://127.0.0.1:8000/api/docs/

### Login Credentials

**Admin User:**
- Username: admin
- Password: admin123
- Role: SuperAdmin

**Regular User:**
- Username: user1
- Password: user123
- Role: Viewer

### Quick Commands Reference

```bash
# Start server
python manage.py runserver

# Create new migrations (after model changes)
python manage.py makemigrations

# Apply migrations to database
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Access Django shell
python manage.py shell

# Collect static files (for production)
python manage.py collectstatic
```

### Troubleshooting

**Port Already in Use:**
If port 8000 is busy, use:
```bash
python manage.py runserver 8080
```

**Database Issues:**
Reset database by deleting `db.sqlite3` and running migrations again.

**Dependencies Issues:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Project Structure Overview

```
it_management_platform/
├── backend/                 # Django project root
│   ├── manage.py           # Django management script
│   ├── requirements.txt    # Python dependencies
│   ├── config/             # Django configuration
│   ├── apps/               # Django apps
│   └── templates/          # HTML templates
└── setup_database.py       # Database setup script
```

The application will be available at http://127.0.0.1:8000/ once the server is running!

