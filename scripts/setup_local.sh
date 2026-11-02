#!/usr/bin/env bash
# ==============================================================================
# Small Shop Inventory Management System - Local Setup Script
# ==============================================================================
set -e

echo "=================================================================="
echo "  Setting up Small Shop Inventory Management System (Local Dev)   "
echo "=================================================================="

# 1. Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed. Please install Python 3.10+."
    exit 1
fi

echo "✓ Python version: $(python3 --version)"

# 2. Create Virtual Environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment in ./venv..."
    python3 -m venv venv
fi

# 3. Activate Virtual Environment
source venv/bin/activate
echo "✓ Virtual environment activated."

# 4. Install Dependencies
echo "Installing project dependencies..."
pip install --upgrade pip
pip install -r requirements-dev.txt
echo "✓ All dependencies installed successfully."

# 5. Initialize Local SQLite Database & Seed Data
echo "Initializing local database with sample inventory..."
python scripts/init_db.py

# 6. Run Automated Test Suite
echo "Running automated test suite..."
pytest -v

echo "=================================================================="
echo "🎉 Setup complete! All systems operational and tests passed."
echo ""
echo "To start the application locally, run:"
echo "  source venv/bin/activate"
echo "  python wsgi.py"
echo ""
echo "Then open your browser at: http://localhost:5000"
echo "Log in with:"
echo "  Username: admin"
echo "  Password: admin123"
echo "=================================================================="
