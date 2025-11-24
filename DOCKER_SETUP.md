# Docker Setup for Gym Membership Chatbot

This guide explains how to run the Gym Membership Chatbot using Docker and Docker Compose.

**Note**: The chatbot now uses **HuggingFace Inference API** instead of Ollama. For setup instructions, see [HUGGINGFACE_SETUP.md](./HUGGINGFACE_SETUP.md).

## Prerequisites

- Docker (version 20.10+)
- Docker Compose (version 2.0+)
- HuggingFace API key (get one at https://huggingface.co/settings/tokens)
- ~1GB RAM available
- ~5GB disk space

## Quick Start

### 1. Configure HuggingFace API Key

```bash
# Create .env file with your HuggingFace API key
cat > .env << EOF
HF_API_KEY=hf_your_token_here
HF_MODEL=mistralai/Mistral-7B-Instruct-v0.2
DEBUG=false
SECRET_KEY=django-insecure-dev-key-change-in-production
EOF
```

Get your API key from: https://huggingface.co/settings/tokens

### 2. Build and Start the Services

```bash
# Navigate to the project directory
cd Gym-Membership-Chatbot

# Build images and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 3. Initialize the Database

```bash
# Run migrations (usually automatic, but can be manual)
docker-compose exec web python manage.py migrate

# Create a superuser (for Django admin)
docker-compose exec web python manage.py createsuperuser
```

### 4. Access the Application

- **Web Interface**: http://localhost:8000
- **Django Admin**: http://localhost:8000/admin
- **Chatbot**: http://localhost:8000/chatbot/

## Service Architecture

### Services in docker-compose.yml

1. **PostgreSQL (db)**
   - Port: 5432
   - Database: gym_db
   - User: gymuser
   - Password: gympass123
   - Volume: `postgres_data`

2. **Redis (redis)**
   - Port: 6379
   - Volume: `redis_data`
   - Used for caching and session storage

3. **Django Web (web)**
   - Port: 8000
   - Gunicorn with 3 workers
   - Volumes: app code, static files, media, logs
   - Depends on: db, redis
   - Uses HuggingFace Inference API (no local model needed)

## Configuration

### Environment Variables

Edit the `environment` section in `docker-compose.yml` or create a `.env` file:

```env
# Django
DEBUG=false
SECRET_KEY=your-secure-key-here

# Database
DATABASE_URL=postgresql://gymuser:gympass123@db:5432/gym_db

# HuggingFace Inference API
HF_API_KEY=hf_your_actual_token_here
HF_MODEL=mistralai/Mistral-7B-Instruct-v0.2

# Redis
REDIS_URL=redis://redis:6379/1

# Security
ALLOWED_HOSTS=localhost,127.0.0.1,web
CSRF_TRUSTED_ORIGINS=http://localhost:8000
```

### Switching Models

To use a different model, update the `HF_MODEL` environment variable:

```bash
# Example: Use Llama 2 (requires license acceptance on HuggingFace)
HF_MODEL=meta-llama/Llama-2-7b-chat-hf

# Example: Use Falcon 7B
HF_MODEL=tiiuae/falcon-7b-instruct

# Example: Use GPT-2 for testing
HF_MODEL=gpt2

# Available models: https://huggingface.co/models
```

**Note**: Make sure your HuggingFace account has access to the model (some require license acceptance). See [HUGGINGFACE_SETUP.md](./HUGGINGFACE_SETUP.md) for details.

## Common Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f ollama
docker-compose logs -f db

# Last 50 lines
docker-compose logs --tail=50
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart web
docker-compose restart db
docker-compose restart redis
```

### Stop Services

```bash
# Stop all (but don't remove)
docker-compose stop

# Stop and remove containers
docker-compose down

# Remove everything including volumes
docker-compose down -v
```

### Run Management Commands

```bash
# Django management commands
docker-compose exec web python manage.py <command>

# Examples:
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py seed_database  # if available
```

### Check Service Health

```bash
# View all services and their status
docker-compose ps

# Check health endpoint
curl http://localhost:8000/health/

# Check PostgreSQL
docker-compose exec db psql -U gymuser -d gym_db -c "SELECT 1"

# Check Redis
docker-compose exec redis redis-cli ping
```

## Troubleshooting

### HuggingFace API Key Not Working

**Problem**: "HuggingFace API key not configured" or "Invalid API key"

**Solutions**:
1. Verify your API key: https://huggingface.co/settings/tokens
2. Check environment variable is set:
   ```bash
   docker-compose exec web printenv | grep HF_API_KEY
   ```
3. Update `.env` file or environment variables
4. Restart the service: `docker-compose restart web`

### Database Connection Issues

**Problem**: "Cannot connect to database" error

**Solutions**:
1. Check PostgreSQL health: `docker-compose ps db`
2. View logs: `docker-compose logs db`
3. Wait for database to be ready (first startup can take 10-20s)
4. Restart database: `docker-compose restart db`

### Out of Memory

**Problem**: Services are killed or not starting

**Solutions**:
1. Increase Docker memory limit (Docker Desktop → Preferences → Resources)
2. Stop other applications
3. Reduce number of Gunicorn workers in `Dockerfile.ollama`:
   ```dockerfile
   --workers 2  # Instead of 3
   ```

### Port Already in Use

**Problem**: "Port 8000 is already allocated"

**Solutions**:
1. Kill the process using the port: `lsof -i :8000`
2. Change port in docker-compose.yml: `ports: - "8001:8000"`
3. Stop other containers: `docker-compose down`

## HuggingFace Inference Acceleration

HuggingFace handles model inference on their optimized servers, so:

✅ **No GPU setup needed** - HuggingFace uses their GPU infrastructure
✅ **No local acceleration required** - Models are pre-optimized
✅ **Better performance** - Professional-grade hardware
✅ **Easy updates** - Model updates handled server-side

For faster responses, you can upgrade to **HuggingFace Pro** ($9/month) which provides:
- Higher rate limits
- Priority GPU access
- Better uptime guarantees

## Performance Tuning

### Gunicorn Workers

Adjust workers based on CPU cores:
```dockerfile
# In Dockerfile.ollama CMD
--workers 4  # 2 × CPU cores + 1 (for 2-core systems: 5)
```

### HuggingFace Model Selection

| Model | Speed | Quality | Free Tier | Notes |
|-------|-------|---------|-----------|-------|
| Mistral 7B | ⚡ Fast | ⭐⭐⭐⭐ | ✅ Yes | **Recommended** |
| Llama 2 | ⚡ Fast | ⭐⭐⭐⭐⭐ | ✅ Yes* | Requires license |
| Falcon 7B | ⚡⚡ Very Fast | ⭐⭐⭐⭐ | ✅ Yes | Good alternative |
| GPT-2 | ⚡⚡⚡ Ultra Fast | ⭐⭐⭐ | ✅ Yes | Testing only |

See [HUGGINGFACE_SETUP.md](./HUGGINGFACE_SETUP.md) for detailed model comparison.

## Production Deployment

### On Render.com

The HuggingFace Inference API is perfect for Render:

1. Set environment variables in Render dashboard:
   - `HF_API_KEY`: Your HuggingFace token
   - `HF_MODEL`: Your chosen model
2. Deploy normally - no special configuration needed
3. All inference happens on HuggingFace servers

See `RENDER_SETUP.md` for detailed Render deployment instructions.

### On Other Platforms

For AWS, GCP, Azure, or your own server:
1. Ensure sufficient resources (2GB+ RAM, 5GB+ disk)
2. Use Docker Compose or Docker Swarm
3. Set up persistent volumes for database
4. Use environment variables for secrets (including HF_API_KEY)
5. Set up health checks and monitoring

## Security Considerations

⚠️ **Development Configuration**:
- Default credentials are not secure
- Change `SECRET_KEY` in production
- Update database password
- Set `DEBUG=false` in production
- Use strong ALLOWED_HOSTS configuration

For production, see Django security documentation:
https://docs.djangoproject.com/en/stable/howto/deployment/checklist/

## Monitoring

### View Real-time Logs

```bash
# Follow all logs with timestamps
docker-compose logs -f --timestamps

# Filter by service
docker-compose logs -f web --tail=100
```

### Container Resource Usage

```bash
docker stats
```

### Database Backups

```bash
# Backup PostgreSQL
docker-compose exec db pg_dump -U gymuser gym_db > backup.sql

# Restore from backup
docker-compose exec -T db psql -U gymuser gym_db < backup.sql
```

## Development Workflow

### Make Code Changes

1. Edit files locally (they're mounted in the container)
2. Django auto-reloads in debug mode
3. No need to rebuild unless you change requirements or settings

### Add Python Packages

```bash
# Add to requirements.txt, then:
docker-compose up -d --build web
```

### Run Tests

```bash
docker-compose exec web python manage.py test
```

### Shell Access

```bash
# Django shell
docker-compose exec web python manage.py shell

# Bash in container
docker-compose exec web bash

# Postgres
docker-compose exec db psql -U gymuser gym_db
```

## FAQ

**Q: How long does the first startup take?**
A: 5-15 minutes due to model pulling. Subsequent startups are fast (~30s).

**Q: Can I use a different database?**
A: Yes. Update `DATABASE_URL` in docker-compose.yml or environment variables. Supports PostgreSQL, MySQL, etc.

**Q: Will my data persist?**
A: Yes, as long as you don't run `docker-compose down -v`. Volumes are persistent.

**Q: How do I backup my data?**
A: Use Docker volume backups or database dumps. See "Monitoring" section.

**Q: Can I use this in production?**
A: Yes, but with proper security hardening. See "Production Deployment" section.

## Additional Resources

- Docker Documentation: https://docs.docker.com/
- Docker Compose Reference: https://docs.docker.com/compose/compose-file/
- HuggingFace Inference API: https://huggingface.co/docs/inference-api
- Django Deployment Checklist: https://docs.djangoproject.com/en/stable/howto/deployment/checklist/
- HuggingFace Setup Guide: [HUGGINGFACE_SETUP.md](./HUGGINGFACE_SETUP.md)

## Support

For issues:
1. Check logs: `docker-compose logs`
2. Review this guide
3. Check project issues on GitHub
4. Ask in the project discussions
