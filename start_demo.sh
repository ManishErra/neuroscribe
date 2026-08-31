#!/usr/bin/env bash
# NeuroScribe Local Demo Startup Script

echo "=========================================="
echo "  NeuroScribe Local Demo Startup"
echo "=========================================="
echo ""

if [ -f "client/.env" ]; then
    sed -i "s|^VITE_API_URL=.*|VITE_API_URL=http://localhost:8000|" client/.env
    echo "[OK] Frontend API URL set to http://localhost:8000"
fi

if [ -f "backend/.env" ]; then
    sed -i "s|^CORS_ALLOWED_ORIGINS=.*|CORS_ALLOWED_ORIGINS=|" backend/.env
    echo "[OK] Backend CORS set to local defaults (http://localhost:5173)"
fi

echo ""
echo "STARTUP COMMANDS:"
echo ""
echo "  TERMINAL 1 (Backend):"
echo "  cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000"
echo ""
echo "  TERMINAL 2 (Frontend):"
echo "  cd client && npm run dev"
echo ""
echo "=========================================="
echo "  LOCAL DEMO URL:"
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "=========================================="
echo ""
