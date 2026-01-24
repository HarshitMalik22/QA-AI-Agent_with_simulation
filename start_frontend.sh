#!/bin/bash
# Start frontend server

cd frontend
echo "Starting QA Digital Twin Frontend..."
echo "Installing dependencies..."
npm install > /dev/null 2>&1
echo "Starting development server on http://localhost:3000"
npm start
