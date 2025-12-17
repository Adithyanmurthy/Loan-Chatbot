@echo off
echo Starting AI Loan Chatbot Development Environment...

echo Starting Mock APIs...
cd mock-apis
start "Mock APIs" cmd /k "npm install && npm start"
cd ..

timeout /t 3 /nobreak >nul

echo Starting Backend...
cd backend
start "Backend" cmd /k "pip install -r requirements.txt && python app.py"
cd ..

timeout /t 3 /nobreak >nul

echo Starting Frontend...
cd frontend
start "Frontend" cmd /k "npm install && npm start"
cd ..

echo All services started!
echo Frontend: http://localhost:3000
echo Backend: http://localhost:5000
echo CRM API: http://localhost:3001
echo Credit Bureau API: http://localhost:3002
echo Offer Mart API: http://localhost:3003

pause