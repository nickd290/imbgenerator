#!/bin/bash
# Railway startup script for IMB Generator
# Runs database migrations before starting the application

set -e  # Exit on error

echo "================================"
echo "IMB Generator - Starting Up"
echo "================================"

# Run database migrations
echo "Running database migrations..."
flask db upgrade

# Check if migrations succeeded
if [ $? -eq 0 ]; then
    echo "✅ Database migrations completed successfully"
else
    echo "❌ Database migrations failed"
    exit 1
fi

# Start the application
echo "Starting Gunicorn server..."
exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 4 --timeout 120
