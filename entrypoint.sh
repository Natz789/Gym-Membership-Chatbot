#!/bin/bash

# Entrypoint script for Gym Membership Chatbot with Ollama
# This script manages both Ollama and Django startup

set -e

echo "================================"
echo "Starting Gym Membership Chatbot"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to log messages
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Wait for a service to be ready
wait_for_service() {
    local host=$1
    local port=$2
    local service=$3
    local timeout=${4:-60}
    local elapsed=0

    log_info "Waiting for $service to be ready ($host:$port)..."

    while ! nc -z "$host" "$port" 2>/dev/null; do
        if [ $elapsed -ge $timeout ]; then
            log_error "$service did not become ready within ${timeout}s"
            return 1
        fi
        sleep 1
        elapsed=$((elapsed + 1))
    done

    log_info "$service is ready!"
    return 0
}

# 1. Start Ollama service
log_info "Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!
log_info "Ollama process started (PID: $OLLAMA_PID)"

# Wait for Ollama to be ready
if ! wait_for_service "localhost" "11434" "Ollama" "60"; then
    log_error "Failed to start Ollama service"
    kill $OLLAMA_PID 2>/dev/null || true
    exit 1
fi

# 2. Pull the Ollama model
log_info "Pulling Ollama model: ${OLLAMA_MODEL:-qwen2.5:0.5b}..."
MODEL=${OLLAMA_MODEL:-qwen2.5:0.5b}

# Add timeout to model pull (3600 seconds = 1 hour max)
if timeout 3600 ollama pull "$MODEL"; then
    log_info "Model pulled successfully: $MODEL"
else
    log_warning "Failed to pull model $MODEL (timeout or error)"
fi

# 3. Wait for database to be ready
log_info "Waiting for PostgreSQL database..."
if ! wait_for_service "db" "5432" "PostgreSQL" "60"; then
    log_warning "PostgreSQL not responding, continuing anyway..."
fi

# 4. Wait for Redis to be ready
log_info "Waiting for Redis..."
if ! wait_for_service "redis" "6379" "Redis" "30"; then
    log_warning "Redis not responding, continuing anyway..."
fi

# 5. Run Django migrations
log_info "Running Django database migrations..."
python manage.py migrate --noinput || log_warning "Migration completed with warnings"

# 6. Create cache table
log_info "Creating cache table..."
python manage.py createcachetable || log_warning "Cache table creation skipped (may already exist)"

# 7. Collect static files (in production)
if [ "$DEBUG" = "false" ]; then
    log_info "Collecting static files..."
    python manage.py collectstatic --noinput || log_warning "Static files collection skipped"
fi

# 8. Create superuser if it doesn't exist (optional, for development)
if [ "$CREATE_SUPERUSER" = "true" ]; then
    log_info "Creating superuser..."
    python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print("Superuser created: admin / admin")
else:
    print("Superuser already exists")
END
fi

# 9. Start Django with Gunicorn
log_info "Starting Django application with Gunicorn..."
log_info "Listening on 0.0.0.0:8000"
log_info "Ollama available at http://ollama:11434"

# Run gunicorn
exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --worker-class sync \
    --worker-tmp-dir /dev/shm \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    gym_project.wsgi:application

# Note: exec replaces the shell process with gunicorn,
# so Ollama will continue running in the background
