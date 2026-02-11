# Render Deployment Guide for IT Management Platform

## Prerequisites
- Python 3.11 or 3.12 (3.13 requires Django 4.2.11+)
- Git repository with your code
- Render account

## Quick Deployment Steps

### 1. Prepare Your Local Environment

```bash
# Navigate to backend directory
cd it_management_platform/backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip wheel

# Install dependencies
pip install -r requirements.txt

# Create .env file for local development
echo "DJANGO_SECRET_KEY=your-secret-key-here" > .env
echo "DEBUG=True" >> .env
echo "RENDER=False" >> .env

# Run migrations
python manage.py migrate

# Test the server
python manage.py runserver
```

### 2. Configure Render Environment Variables

In your Render dashboard, set these environment variables:

```
PYTHON_VERSION=3.11

RENDER=true

DJANGO_SETTINGS_MODULE=config.settings.render

DJANGO_SECRET_KEY=<generate-a-secure-random-string>

# PostgreSQL - Render will provide this automatically
DATABASE_URL=<provided-by-render>

# Redis (optional) - Render will provide if you use the Blueprint
REDIS_URL=<provided-by-render>

# Email Configuration (optional)
EMAIL_HOST=smtp.sendgrid.net
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=<your-sendgrid-api-key>
DEFAULT_FROM_EMAIL=noreply@your-domain.com
```

### 3. Deploy to Render

#### Option A: Connect GitHub Repository (Recommended)

1. **Create a new Web Service on Render:**
   - Go to https://dashboard.render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure the service:**
   - Name: `it-management-backend`
   - Environment: `Python`
   - Region: `Oregon (US West)` or `Frankfurt (EU Central)`
   - Branch: `main`
   - Runtime: `Python 3`

3. **Build Command:**
   ```bash
   python -m venv .venv
   .venv/bin/pip install --upgrade pip wheel
   .venv/bin/pip install -r requirements.txt
   ```

4. **Start Command:**
   ```bash
   .venv/bin/gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120
   ```

5. **Environment Variables:**
   Add the variables listed in Section 2.

6. **Click "Create Web Service"**

#### Option B: Use Render Blueprint

1. **Create `render.yaml`** (already created in backend directory)

2. **Deploy:**
   - Go to https://dashboard.render.com/blueprints
   - Click "New +" → "Blueprint"
   - Connect your repository
   - Review and apply the Blueprint

### 4. Database Setup

If using PostgreSQL (Render's default):

```bash
# Connect to your Render PostgreSQL
# Run migrations after deployment
python manage.py migrate
```

### 5. Create Superuser

After deployment, create an admin superuser:

```bash
# Use Django shell
python manage.py shell

# Or create via management command
python manage.py createsuperuser
```

## Files Modified for Render Deployment

### 1. `requirements.txt`
- Updated Django to 4.2.11 (Python 3.13 compatibility)
- Kept pytest-django at 4.7.0
- All dependencies are Python 3.11+ compatible

### 2. `config/settings/render.py` (NEW)
- Render-specific production settings
- PostgreSQL configuration via `dj_database_url`
- Redis cache configuration
- WhiteNoise for static files
- Production security settings

### 3. `config/wsgi.py`
- Updated to use render settings when `RENDER=true`
- Clean WSGI configuration

### 4. `render.yaml` (NEW)
- Blueprint for Render services
- Includes PostgreSQL and Redis

## Troubleshooting

### ModuleNotFoundError: No module named 'pkg_resources'

This error occurs because `setuptools` is missing or outdated:

```bash
# In requirements.txt, ensure setuptools is NOT pinned to <81
# The problematic line was: setuptools<81
# This has been removed from requirements.txt

# If still failing, add this to requirements.txt:
setuptools>=70.0.0
```

### psycopg2 installation fails

Render provides PostgreSQL, but `psycopg2` may fail to compile:

```bash
# Use psycopg2-binary instead (pure Python, slower but works)
# Already updated in requirements.txt
psycopg2-binary>=2.9.9
```

### Static files not loading

WhiteNoise should handle static files automatically. If not:

```bash
# Collect static files
python manage.py collectstatic --noinput
```

### CORS errors

Add your frontend URL to `CORS_ALLOWED_ORIGINS` in `render.py`:

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://your-frontend.onrender.com",
]
```

### 502 Bad Gateway

This usually means Gunicorn isn't starting correctly:

1. Check your start command syntax
2. Ensure `DJANGO_SETTINGS_MODULE` is set correctly
3. Check logs for specific errors:
   ```bash
   # View logs in Render dashboard
   # Or locally:
   .venv/bin/gunicorn config.wsgi:application --bind 0.0.0.0:8000 --reload
   ```

### Database connection errors

1. Ensure `DATABASE_URL` is set correctly
2. Check that migrations have run:
   ```bash
   python manage.py showmigrations
   python manage.py migrate
   ```

## Production Checklist

- [ ] Django SECRET_KEY is secure and not in version control
- [ ] DEBUG is set to False
- [ ] ALLOWED_HOSTS includes your domain
- [ ] HTTPS is enforced
- [ ] Database credentials are secure
- [ ] Environment variables are set in Render dashboard
- [ ] Static files are served via WhiteNoise
- [ ] Logging is configured appropriately
- [ ] Email settings are configured (optional)
- [ ] Backups are enabled for PostgreSQL

## Rollback Procedure

If deployment fails:

1. **From Render Dashboard:**
   - Go to your service
   - Click "History"
   - Select a previous deployment
   - Click "Deploy"

2. **Via Git:**
   ```bash
   git revert <bad-commit>
   git push origin main
   ```

## Monitoring

- **Health Check:** `https://your-service.onrender.com/health/`
- **Logs:** Available in Render dashboard
- **Metrics:** CPU, memory, response times in dashboard

## Security Considerations

1. **Keep dependencies updated:**
   ```bash
   pip install --upgrade django djangorestframework
   ```

2. **Use environment variables for secrets**

3. **Enable HTTPS redirect (already in settings)**

4. **Use secure cookies (already in settings)**

5. **Regular backups enabled for database**

## Support

- Render Documentation: https://render.com/docs
- Django Documentation: https://docs.djangoproject.com/
- Issues? Check Render service logs first

