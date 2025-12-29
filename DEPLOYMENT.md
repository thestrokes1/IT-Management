# IT Management Platform - Production Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the IT Management Platform to production environments, with specific focus on PythonAnywhere but adaptable to other platforms.

## Prerequisites
- Python 3.8+ installed
- PostgreSQL or MySQL database
- Domain name (optional, can use PythonAnywhere subdomain)
- SSL certificate (recommended for production)

## Deployment Steps

### 1. Server Setup

#### PythonAnywhere Deployment
1. Create a PythonAnywhere account at https://www.pythonanywhere.com/
2. Create a new web app:
   - Choose "Manual configuration"
   - Select Python 3.8 or later
   - Note your username and domain

#### Manual Server Deployment
1. Set up a Linux server (Ubuntu 20.04+ recommended)
2. Install required packages:
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv nginx postgresql postgresql-contrib
   ```

### 2. Application Setup

#### On PythonAnywhere:
1. Open a Bash console
2. Clone your repository:
   ```bash
   git clone https://github.com/yourusername/it-management-platform.git
   cd it-management-platform/backend
   ```

3. Create a virtual environment:
   ```bash
   python3.8 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

#### On Manual Server:
1. Set up virtual environment and install dependencies:
   ```bash
   cd /var/www/it-management-platform
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### 3. Database Setup

#### PostgreSQL Configuration
1. Create database:
   ```sql
   CREATE DATABASE it_management_db;
   CREATE USER it_management_user WITH PASSWORD 'your_secure_password';
   GRANT ALL PRIVILEGES ON DATABASE it_management_db TO it_management_user;
   ```

2. Update settings to use PostgreSQL:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'it_management_db',
           'USER': 'it_management_user',
           'PASSWORD': 'your_secure_password',
           'HOST': 'localhost',
           'PORT': '5432',
       }
   }
   ```

### 4. Environment Configuration

1. Create `.env` file:
   ```bash
   cp .env.example .env
   ```

2. Update `.env` with production values:
   ```env
   DEBUG=False
   SECRET_KEY=your-super-secret-production-key
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   DATABASE_URL=postgresql://it_management_user:your_secure_password@localhost/it_management_db
   EMAIL_HOST=smtp.gmail.com
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   ```

### 5. Static Files Configuration

#### For PythonAnywhere:
1. In the web app configuration:
   - Static files mapping:
     - URL: `/static/`
     - Directory: `/home/yourusername/it-management-platform/backend/staticfiles/`

2. Run collectstatic:
   ```bash
   python manage.py collectstatic --noinput
   ```

#### For Manual Server:
1. Configure Nginx for static files:
   ```nginx
   location /static/ {
       alias /var/www/it-management-platform/backend/staticfiles/;
   }
   ```

2. Collect static files:
   ```bash
   python manage.py collectstatic --noinput
   ```

### 6. Database Migrations

1. Run migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. Create superuser:
   ```bash
   python manage.py createsuperuser
   ```

3. Load initial data (optional):
   ```bash
   python manage.py loaddata initial_data.json
   ```

### 7. Web Server Configuration

#### PythonAnywhere WSGI Configuration
Update `/var/www/yourusername_pythonanywhere_com_wsgi.py`:
```python
import os
import sys

# Add project directory to path
path = '/home/yourusername/it-management-platform/backend'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.prod'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

#### Manual Server Nginx Configuration
Create `/etc/nginx/sites-available/it-management-platform`:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location /static/ {
        alias /var/www/it-management-platform/backend/staticfiles/;
    }

    location /media/ {
        alias /var/www/it-management-platform/backend/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/it-management-platform /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 8. SSL Configuration (Production)

#### Using Let's Encrypt (Manual Server):
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 9. Process Management

#### Using Gunicorn:
Create systemd service `/etc/systemd/system/it-management-platform.service`:
```ini
[Unit]
Description=IT Management Platform
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/it-management-platform/backend
Environment="PATH=/var/www/it-management-platform/backend/venv/bin"
ExecStart=/var/www/it-management-platform/backend/venv/bin/gunicorn --workers 3 --bind unix:/var/www/it-management-platform/backend/it_management_platform.sock config.wsgi:application

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable it-management-platform
sudo systemctl start it-management-platform
sudo systemctl status it-management-platform
```

### 10. Monitoring and Maintenance

#### Log Rotation
Add to `/etc/logrotate.d/it-management-platform`:
```
/var/www/it-management-platform/backend/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
}
```

#### Backup Script
Create `/home/backup/it-management-platform-backup.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/home/backup"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
pg_dump it_management_db > $BACKUP_DIR/db_backup_$DATE.sql

# Media files backup
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz /var/www/it-management-platform/backend/media/

# Keep only last 7 days of backups
find $BACKUP_DIR -type f -mtime +7 -delete
```

Add to crontab:
```bash
0 2 * * * /home/backup/it-management-platform-backup.sh
```

## Troubleshooting

### Common Issues:
1. **Static files not loading**: Check static files mapping and run `collectstatic`
2. **Database connection errors**: Verify DATABASE_URL and database credentials
3. **Permission errors**: Ensure proper file permissions (644 for files, 755 for directories)
4. **Import errors**: Check virtual environment activation and Python path

### Health Checks:
1. Test application: `curl http://yourdomain.com/`
2. Check logs: `tail -f /var/www/it-management-platform/backend/logs/django.log`
3. Verify database: `python manage.py dbshell`
4. Check system status: `sudo systemctl status it-management-platform`

## Security Checklist
- [ ] DEBUG=False in production
- [ ] Strong SECRET_KEY generated
- [ ] ALLOWED_HOSTS configured
- [ ] HTTPS enabled
- [ ] Database credentials secured
- [ ] File permissions set correctly
- [ ] Regular backups configured
- [ ] Log monitoring enabled
- [ ] Security headers implemented
- [ ] Rate limiting configured

## Performance Optimization
- [ ] Database indexes created
- [ ] Static files compressed
- [ ] Caching configured (Redis/Memcached)
- [ ] CDN configured for static files
- [ ] Database connection pooling enabled
- [ ] Gunicorn workers optimized
- [ ] Nginx gzip compression enabled

