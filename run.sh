#!/bin/bash

# IMB Generator - Development Server Startup Script

echo "========================================="
echo "  IMB Generator - Development Server"
echo "========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import flask" 2>/dev/null; then
    echo "❌ Dependencies not installed!"
    echo "Installing dependencies..."
    pip install -r requirements.txt
    echo "✅ Dependencies installed"
    echo ""
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your API credentials before processing files!"
    echo ""
fi

# Create uploads directory if it doesn't exist
mkdir -p uploads

# Start the application
echo "========================================="
echo "  Starting Flask development server..."
echo "========================================="
echo ""
echo "📍 Server will be running at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python app.py
