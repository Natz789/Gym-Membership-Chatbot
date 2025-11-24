# Gym Membership System Chatbot - Render Deployment Guide

This guide provides comprehensive instructions to deploy the Gym Membership System Chatbot on Render.com with PostgreSQL database support.

## Overview

- **Framework**: Django 5.2.7
- **Database**: PostgreSQL
- **Web Server**: Gunicorn
- **Chatbot Engine**: Ollama (Qwen2.5-0.5B)
- **Static Files**: WhiteNoise
- **Deployment Platform**: Render.com

---

## Prerequisites

Before deploying, ensure you have:

1. A [Render.com](https://render.com) account
2. Access to your GitHub repository
3. The PostgreSQL credentials provided:
   - **Database Name**: `gym_4iym`
   - **Database User**: `gym_4iym_user`
   - **Password**: `kSZlA71WuWG7R9srM0yk3hzs1GbO8Ts6`
   - **Host**: `dpg-d4hgpcruibrs73djpc7g-a.singapore-postgres.render.com` (External)
   - **Port**: `5432`

---

## Step 1: Prepare Your Repository

Make sure the following files are in your project root:

- ✅ `requirements.txt` - Python dependencies
- ✅ `build.sh` - Build script for Render
- ✅ `Dockerfile` - Docker configuration
- ✅ `render.yaml` - Render configuration (alternative: use UI)
- ✅ `.env.example` - Environment variables template
- ✅ `manage.py` - Django management script
- ✅ `gym_project/settings.py` - Updated for production

---

## Step 2: Create Environment Variables

Create a `.env` file in your local project (not committed to git):

```bash
# Django Settings
DEBUG=false
SECRET_KEY=your-secure-secret-key-here-minimum-50-chars

# Database Configuration
DATABASE_URL=postgresql://gym_4iym_user:kSZlA71WuWG7R9srM0yk3hzs1GbO8Ts6@dpg-d4hgpcruibrs73djpc7g-a.singapore-postgres.render.com/gym_4iym

# Allowed Hosts
ALLOWED_HOSTS=gym-membership-chatbot.onrender.com,127.0.0.1,localhost

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:0.5b
OLLAMA_TIMEOUT=30

# Redis (optional, for caching)
REDIS_URL=redis://localhost:6379/1

# CSRF and Security
CSRF_TRUSTED_ORIGINS=https://gym-membership-chatbot.onrender.com
```

### Generate a Secure Secret Key

Run this command locally:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## Step 3: Deploy Using Render Web Interface

### Option A: Using render.yaml (Recommended)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Setup Render deployment configuration"
   git push origin claude/setup-gym-database-01LRDme6DVDr6t4PD3hih7kb
   ```

2. **Create Pull Request** on GitHub and merge to main branch

3. **Connect to Render**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will automatically detect `render.yaml`
   - Review settings and click "Create Web Service"

### Option B: Using Render Web UI (Manual)

1. **Create Web Service**
   - Dashboard → "New +" → "Web Service"
   - Select your GitHub repository
   - Configure:
     - **Name**: `gym-membership-chatbot`
     - **Environment**: `Python 3`
     - **Build Command**: `bash build.sh`
     - **Start Command**: `gunicorn gym_project.wsgi:application`
     - **Plan**: Free or Starter

2. **Set Environment Variables**
   - In the web service settings, click "Environment"
   - Add these variables:

   | Key | Value |
   |-----|-------|
   | `DEBUG` | `false` |
   | `SECRET_KEY` | `(generate new)` |
   | `DATABASE_URL` | `postgresql://gym_4iym_user:kSZlA71WuWG7R9srM0yk3hzs1GbO8Ts6@dpg-d4hgpcruibrs73djpc7g-a.singapore-postgres.render.com/gym_4iym` |
   | `ALLOWED_HOSTS` | `gym-membership-chatbot.onrender.com,127.0.0.1,localhost` |
   | `OLLAMA_HOST` | `http://localhost:11434` |
   | `OLLAMA_MODEL` | `qwen2.5:0.5b` |
   | `CSRF_TRUSTED_ORIGINS` | `https://gym-membership-chatbot.onrender.com` |

3. **Create Web Service**
   - Click "Create Web Service"
   - Render will build and deploy your application

---

## Step 4: Configure PostgreSQL Connection

Your PostgreSQL database is already set up with these credentials:

```
Host: dpg-d4hgpcruibrs73djpc7g-a.singapore-postgres.render.com
Port: 5432
Database: gym_4iym
User: gym_4iym_user
Password: kSZlA71WuWG7R9srM0yk3hzs1GbO8Ts6
```

**No additional setup needed** - The `build.sh` script will automatically run migrations.

### Verify Database Connection

After deployment, check the logs:
1. Go to your web service in Render Dashboard
2. Click "Logs" tab
3. Look for successful migration messages:
   ```
   Running database migrations...
   Running migrations
   No migrations to apply.
   ```

---

## Step 5: Test Your Deployment

Once deployment completes:

1. **Check Deployment Status**
   - Render Dashboard → Your service → "Events" tab
   - Look for "Build succeeded" and "Deploy live" messages

2. **Test Application**
   - Visit: `https://gym-membership-chatbot.onrender.com`
   - You should see your application homepage

3. **Check Admin Panel**
   - Visit: `https://gym-membership-chatbot.onrender.com/admin`
   - Login with Django superuser credentials

4. **Test Database Connection**
   - Visit: `https://gym-membership-chatbot.onrender.com/api/health`
   - Should return database status

---

## Step 6: Create Django Superuser (Admin)

After first deployment:

1. **Using Render Console**
   - In your web service, click "Shell"
   - Run:
     ```bash
     python manage.py createsuperuser
     ```
   - Follow prompts to create admin account

2. **Or using SSH**
   - Use Render's SSH access if enabled
   - Run the same command above

---

## Project Structure

```
Gym-Membership-System-Chatbot/
├── gym_project/
│   ├── settings.py          # Production-ready settings
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── gym_app/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── migrations/
├── templates/               # HTML templates
├── static/                  # CSS, JS, images
├── media/                   # User uploads
├── manage.py
├── requirements.txt         # Python dependencies
├── build.sh                 # Build script
├── Dockerfile               # Docker configuration
├── render.yaml              # Render configuration
├── .env.example             # Environment variables template
└── db.sqlite3               # Local development DB (not deployed)
```

---

## Configuration Files Explained

### requirements.txt
Lists all Python package dependencies. Key packages:
- `Django==5.2.7` - Web framework
- `psycopg2-binary` - PostgreSQL adapter
- `gunicorn` - WSGI HTTP server
- `python-decouple` - Environment variable management
- `whitenoise` - Static file serving
- `django-redis` - Caching backend
- `ollama` - Chatbot engine
- `qrcode` - QR code generation
- `Pillow` - Image processing

### build.sh
Render executes this during build:
```bash
#!/bin/bash
pip install -r requirements.txt          # Install dependencies
mkdir -p staticfiles media logs          # Create directories
python manage.py collectstatic --noinput # Collect static files
python manage.py migrate                 # Run migrations
python manage.py createcachetable || true
```

### Dockerfile
Defines container setup:
- Uses Python 3.11 slim image
- Installs system dependencies
- Sets up application environment
- Runs build script
- Exposes port 10000
- Starts Gunicorn server

### render.yaml
Infrastructure as Code for Render:
- Defines web service configuration
- Sets environment variables
- Configures build and start commands
- Mounts persistent disk for media files
- Auto-deploys on push

### gym_project/settings.py
Production-ready Django settings:
- Reads environment variables via `decouple`
- Supports PostgreSQL for production
- Supports SQLite for development
- Static file serving with WhiteNoise
- Security middleware enabled
- Debug mode configurable

---

## Common Issues and Solutions

### Issue 1: Build Fails with "Module Not Found"

**Solution**: Add missing package to `requirements.txt`:
```bash
pip freeze | grep package_name >> requirements.txt
git push
```

### Issue 2: Static Files Not Loading (404)

**Solution**: Ensure WhiteNoise is in middleware:
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Must be here
    ...
]
```

### Issue 3: Database Connection Refused

**Solution**: Verify `DATABASE_URL` is correct:
```bash
# Check in Render logs
echo $DATABASE_URL
```

### Issue 4: "DisallowedHost" Error

**Solution**: Update `ALLOWED_HOSTS` in environment:
```
ALLOWED_HOSTS=your-service-name.onrender.com,127.0.0.1,localhost
```

### Issue 5: Ollama Not Running

**Solution**:
- Ollama requires CPU, not available on free tier
- Run Ollama separately or use OpenAI API instead
- Update `OLLAMA_HOST` to your Ollama server

### Issue 6: Media Files Persist Problem

**Solution**: Use Render Disk for media:
```yaml
# In render.yaml
disk:
  name: gym-data
  mountPath: /opt/render/project/data
```

---

## Updating Your Application

### Deploy New Changes

```bash
# Make changes locally
git add .
git commit -m "Your changes"
git push origin claude/setup-gym-database-01LRDme6DVDr6t4PD3hih7kb

# Render automatically rebuilds and redeploys
```

### Monitor Deployment

1. Go to Render Dashboard
2. Select your web service
3. Click "Events" to see build progress
4. Click "Logs" to see runtime logs

---

## Performance Optimization

### Enable Caching
Uncomment in `gym_project/settings.py`:
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### Database Connection Pooling
Already configured in `settings.py`:
```python
'CONN_MAX_AGE': 600,
'CONN_HEALTH_CHECKS': True,
```

### Static File Compression
WhiteNoise is configured for compression:
```python
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

---

## Security Considerations

### ✅ Implemented

- `DEBUG = False` in production
- HTTPS enforced
- CSRF protection enabled
- Secure headers via SecurityMiddleware
- SQL injection prevention (Django ORM)
- XSS protection (templates)
- Database password not in code

### 🔒 Recommendations

1. **Regenerate SECRET_KEY**
   ```python
   SECRET_KEY = 'your-new-secure-key'
   ```

2. **Use Strong Database Password**
   - Change `gym_4iym_user` password regularly

3. **Enable HTTPS Only**
   - Render automatically provides HTTPS

4. **Set SECURE_HSTS_SECONDS** (optional):
   ```python
   SECURE_HSTS_SECONDS = 31536000
   ```

5. **Regular Backups**
   - Use Render backups for PostgreSQL

---

## Database Management

### Backup Your Database

Render provides automated backups:
1. Go to your database in Render
2. Click "Backups" tab
3. Backups are created daily

### Manual Backup

```bash
pg_dump -h dpg-d4hgpcruibrs73djpc7g-a.singapore-postgres.render.com \
  -U gym_4iym_user -d gym_4iym > backup.sql
```

### Restore from Backup

```bash
psql -h dpg-d4hgpcruibrs73djpc7g-a.singapore-postgres.render.com \
  -U gym_4iym_user -d gym_4iym < backup.sql
```

---

## Monitoring and Logging

### View Logs

1. **Render Dashboard**
   - Service → "Logs" tab
   - Real-time log streaming

2. **Logs Include**
   - Build output
   - Migration status
   - Runtime errors
   - Request logs

### Metrics

Monitor your service:
- CPU usage
- Memory usage
- Request count
- Error rate
- Deploy status

---

## Troubleshooting

### Check Service Status

```bash
# Via Render API
curl https://api.render.com/v1/services/{service-id} \
  -H "Authorization: Bearer {api-key}"
```

### View Build Logs

1. Render Dashboard → Your Service
2. Click "Events" tab
3. Click on build ID to see detailed logs

### SSH into Service

```bash
# Using Render Shell (if enabled)
# Dashboard → Service → Shell
# Then run:
python manage.py shell
```

---

## Next Steps

1. ✅ Deploy application
2. ✅ Run migrations
3. ✅ Create superuser
4. ✅ Test all features
5. ✅ Set up monitoring
6. ✅ Configure backup strategy
7. ✅ Document any custom configurations

---

## Support

For issues with:
- **Django**: [Django Documentation](https://docs.djangoproject.com)
- **Render**: [Render Docs](https://render.com/docs)
- **PostgreSQL**: [PostgreSQL Docs](https://www.postgresql.org/docs)
- **Gunicorn**: [Gunicorn Docs](https://gunicorn.org)

---

## Useful Commands

```bash
# Local testing before deployment
python manage.py runserver

# Collect static files
python manage.py collectstatic

# Run migrations
python manage.py migrate

# Create migrations
python manage.py makemigrations

# Database shell
python manage.py dbshell

# Create superuser
python manage.py createsuperuser

# Check deployment readiness
python manage.py check --deploy
```

---

**Last Updated**: 2025-11-23
**Configuration Version**: 1.0
