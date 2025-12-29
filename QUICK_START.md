# IT Management Platform - Quick Start Guide

## How to Run the IT Management Platform

Follow these steps to set up and run the IT Management Platform on your local machine:

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Git (optional, for cloning)
- Terminal/Command Prompt access

### Step 1: Navigate to the Project Directory
```bash
cd it_management_platform
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
```

### Step 3: Activate Virtual Environment
**On Windows:**
```bash
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
source venv/bin/activate
```

### Step 4: Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 5: Setup Database and Initial Data
```bash
cd ..
python setup.py
```
This command will:
- Check system requirements
- Create database migrations
- Apply migrations to database
- Create superuser account (admin/admin123)
- Create sample data for testing
- Collect static files

### Step 6: Test Project Configuration
```bash
cd backend
python manage.py check
```
This should show "System check identified no issues" if everything is working correctly.

### Step 7: Start Development Server
```bash
python manage.py runserver
```

### Step 7: Access the Application
Open your web browser and go to:
- **Main Application**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/
- **API Documentation**: http://127.0.0.1:8000/api/docs/

### Default Login Credentials
- **Username**: admin
- **Password**: admin123

## Alternative Quick Setup (Single Command)
If you want to run everything in sequence:

**On Windows:**
```bash
cd it_management_platform
python -m venv venv
venv\Scripts\activate
cd backend
pip install -r requirements.txt
cd ..
python setup.py
cd backend
python manage.py runserver
```

**On macOS/Linux:**
```bash
cd it_management_platform
python -m venv venv
source venv/bin/activate
cd backend
pip install -r requirements.txt
cd ..
python setup.py
cd backend
python manage.py runserver
```

## What Happens During Setup
1. **System Check**: Verifies Python version and required packages
2. **Database Setup**: Creates SQLite database and applies all migrations
3. **Superuser Creation**: Creates admin account with default credentials
4. **Sample Data**: Creates test data for assets, projects, tickets, and users
5. **Static Files**: Collects and prepares CSS, JavaScript, and other static assets

## Troubleshooting

### If you get "python is not recognized":
- Make sure Python is installed and added to your PATH
- Try using `python3` instead of `python` on Linux/macOS

### If pip install fails:
- Update pip: `python -m pip install --upgrade pip`
- Ensure you have internet connection

### If database errors occur:
- Delete `backend/db.sqlite3` file and run `python setup.py` again
- Make sure you have write permissions in the project directory

### If static files don't load:
- Run `python manage.py collectstatic --noinput` manually
- Make sure you're in the backend directory

## Development Commands

### Run Tests
```bash
cd backend
python manage.py test
```

### Create New Migrations
```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

### Create New Superuser
```bash
cd backend
python manage.py createsuperuser
```

### Access Django Shell
```bash
cd backend
python manage.py shell
```

## Production Deployment
For production deployment, see the DEPLOYMENT.md file which contains detailed instructions for:
- PythonAnywhere deployment
- Manual server setup
- PostgreSQL configuration
- SSL setup
- Process management with Gunicorn and systemd

## Project Structure
```
it_management_platform/
├── backend/                 # Django application
│   ├── manage.py           # Django management script
│   ├── requirements.txt    # Python dependencies
│   └── apps/               # Core modules
├── setup.py               # Automated setup script
├── DEPLOYMENT.md          # Production deployment guide
└── PROJECT_SUMMARY.md     # Complete project overview
```

## Features Available After Setup
- User management with role-based access
- Asset tracking and assignment
- Project and task management
- Ticketing system with SLA tracking
- Comprehensive logging and audit trails
- Modern responsive web interface
- Complete REST API with documentation

## Support
If you encounter issues:
1. Check that all prerequisites are installed
2. Verify Python version (3.8+ required)
3. Ensure virtual environment is activated
4. Check that all dependencies installed successfully
5. Review the console output for specific error messages

The platform is now ready for use! You can start managing IT assets, creating projects, handling tickets, and monitoring system activities through the web interface.

