#!/bin/bash

# AI Loan Chatbot Development Startup Script

echo "Starting AI Loan Chatbot Development Environment..."

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "Port $1 is already in use"
        return 1
    else
        return 0
    fi
}

# Check required ports
echo "Checking ports..."
check_port 3000 || exit 1
check_port 5000 || exit 1
check_port 3001 || exit 1
check_port 3002 || exit 1
check_port 3003 || exit 1

# Start mock APIs in background
echo "Starting Mock APIs..."
cd mock-apis
npm install
npm start &
MOCK_PID=$!
cd ..

# Wait for mock APIs to start
sleep 3

# Start backend in background
echo "Starting Backend..."
cd backend
pip install -r requirements.txt
python app.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend
echo "Starting Frontend..."
cd frontend
npm install
npm start &
FRONTEND_PID=$!
cd ..

echo "All services started!"
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:5000"
echo "CRM API: http://localhost:3001"
echo "Credit Bureau API: http://localhost:3002"
echo "Offer Mart API: http://localhost:3003"

# Wait for user input to stop
echo "Press any key to stop all services..."
read -n 1

# Kill all background processes
echo "Stopping services..."
kill $FRONTEND_PID 2>/dev/null
kill $BACKEND_PID 2>/dev/null
kill $MOCK_PID 2>/dev/null

echo "All services stopped."