#!/bin/bash
# Start backend server

cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

echo "Starting QA Digital Twin Backend..."
echo "Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1
echo "Starting server on http://localhost:8000"
python -m uvicorn main:app --reload
