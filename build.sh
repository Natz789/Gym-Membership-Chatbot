#!/usr/bin/env bash
# Build script for Gym Membership System Chatbot on Render

set -o errexit

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p staticfiles media logs

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Run migrations (skip if database not available)
echo "Running database migrations..."
python manage.py migrate || true

# Create cache table (if using database cache)
echo "Creating cache table..."
python manage.py createcachetable || true

echo "Build completed successfully!"
