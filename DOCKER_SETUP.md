# Docker Setup for Gym Membership Chatbot with Ollama

This guide explains how to run the Gym Membership Chatbot with Ollama using Docker and Docker Compose.

## Prerequisites

- Docker (version 20.10+)
- Docker Compose (version 2.0+)
- At least 8GB RAM available (recommended for Ollama)
- 10GB+ disk space for the Ollama model

## Quick Start

### 1. Build and Start the Services

```bash
# Clone/navigate to the project directory
cd Gym-Membership-Chatbot

# Build images and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 2. Initialize the Database

```bash
# Run migrations (usually automatic, but can be manual)
docker-compose exec web python manage.py migrate

# Create a superuser (for Django admin)
docker-compose exec web python manage.py createsuperuser
```

### 3. Access the Application

- **Web Interface**: http://localhost:8000
- **Django Admin**: http://localhost:8000/admin
- **Chatbot**: http://localhost:8000/chatbot/
- **Ollama API**: http://localhost:11434

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

3. **Ollama (ollama)**
   - Port: 11434
   - Volume: `ollama_data`, `ollama_models`
   - Serves the Qwen2.5-0.5B model via HTTP API
   - **Note**: First startup will pull the model (~4GB) - this can take 5-15 minutes

4. **Django Web (web)**
   - Port: 8000
   - Gunicorn with 3 workers
   - Volumes: app code, static files, media, logs
   - Depends on: db, redis, ollama

## Configuration

### Environment Variables

Edit the `environment` section in `docker-compose.yml` or create a `.env` file:

```env
# Django
DEBUG=false
SECRET_KEY=your-secure-key-here

# Database
DATABASE_URL=postgresql://gymuser:gympass123@db:5432/gym_db

# Ollama
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=qwen2.5:0.5b
OLLAMA_TIMEOUT=60

# Redis
REDIS_URL=redis://redis:6379/1

# Security
ALLOWED_HOSTS=localhost,127.0.0.1,web
CSRF_TRUSTED_ORIGINS=http://localhost:8000
```

### Custom Models

To use a different Ollama model, update the `OLLAMA_MODEL` environment variable:

```bash
# Example: Use a larger model
OLLAMA_MODEL=llama2
# or
OLLAMA_MODEL=mistral

# Available models: https://ollama.ai/library
```

**Note**: Larger models require more RAM and disk space.

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
docker-compose restart ollama
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

# Check Ollama
curl http://localhost:11434/api/tags
```

## Troubleshooting

### Ollama Not Starting

**Problem**: Ollama service fails to start or model fails to pull

**Solutions**:
1. Check logs: `docker-compose logs ollama`
2. Ensure 10GB+ disk space available: `df -h`
3. Increase Docker memory allocation in Docker Desktop settings
4. Try pulling the model manually:
   ```bash
   docker-compose exec ollama ollama pull qwen2.5:0.5b
   ```

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
3. Use a smaller Ollama model: Change `OLLAMA_MODEL=tinyllama`

### Port Already in Use

**Problem**: "Port 8000 is already allocated"

**Solutions**:
1. Kill the process using the port: `lsof -i :8000`
2. Change port in docker-compose.yml: `ports: - "8001:8000"`
3. Stop other containers: `docker-compose down`

## GPU Support (Optional)

If you have an NVIDIA GPU and want to accelerate Ollama:

1. Install NVIDIA Docker Runtime:
   ```bash
   # Ubuntu/Debian
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
     sudo tee /etc/apt/sources.list.d/nvidia-docker.list
   sudo apt-get update && sudo apt-get install -y nvidia-docker2
   ```

2. Uncomment GPU lines in docker-compose.yml:
   ```yaml
   ollama:
     runtime: nvidia
     environment:
       - NVIDIA_VISIBLE_DEVICES=all
   ```

3. Restart: `docker-compose up -d ollama`

## Performance Tuning

### Gunicorn Workers

Adjust workers based on CPU cores:
```dockerfile
# In Dockerfile.ollama CMD
--workers 4  # 2 × CPU cores + 1 (for 2-core systems: 5)
```

### Ollama Model Selection

| Model | Size | RAM | Speed | Quality |
|-------|------|-----|-------|---------|
| tinyllama | 0.5GB | 512MB | Very Fast | Basic |
| qwen2.5:0.5b | 1.4GB | 2GB | Fast | Good |
| mistral | 5GB | 8GB | Moderate | Excellent |
| llama2 | 6B | 10GB | Moderate | Excellent |

## Production Deployment

### On Render.com

See `RENDER_SETUP.md` for deploying to Render.

**Important**: The `docker-compose.yml` with Ollama is resource-intensive. For production on Render:
1. Use the standard Dockerfile (without embedded Ollama)
2. Switch to a cloud LLM API (OpenAI, Groq, HuggingFace)
3. Or use a separate Ollama server/service

### On Other Platforms

For AWS, GCP, Azure, or your own server:
1. Ensure sufficient resources (8GB+ RAM, 10GB+ disk)
2. Use Docker Compose or Docker Swarm
3. Set up persistent volumes for database and Ollama models
4. Use environment variables for secrets
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
- Ollama Documentation: https://github.com/ollama/ollama
- Django Deployment Checklist: https://docs.djangoproject.com/en/stable/howto/deployment/checklist/

## Support

For issues:
1. Check logs: `docker-compose logs`
2. Review this guide
3. Check project issues on GitHub
4. Ask in the project discussions
