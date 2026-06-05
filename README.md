# Technoax Full Stack - Setup & Development Guide

## Project Structure

```
technoax-fullstack/
├── frontend/                 # React/TanStack Start frontend
│   ├── src/
│   │   ├── components/      # UI components & site layout
│   │   ├── routes/          # Page routes
│   │   ├── lib/
│   │   │   └── api/         # API client services
│   │   └── ...
│   ├── package.json
│   └── vite.config.ts
├── backend/                  # FastAPI Python backend
│   ├── main.py              # Application entry point
│   ├── api/                 # Route handlers
│   │   ├── analyze_video.py
│   │   ├── frame_analysis.py
│   │   ├── media_risk_score.py
│   │   └── health.py
│   ├── models/              # ML/data models
│   ├── services/            # Business logic
│   ├── utils/               # Utilities
│   ├── requirements.txt
│   └── .env
├── package.json             # Root package for running both
├── .env                     # Shared environment configuration
└── README.md
```

## Prerequisites

- **Node.js** 18+ (for frontend)
- **Python** 3.8+ (for backend)
- **npm** or **yarn** (for frontend package management)
- **pip** (for Python packages)

## Installation

### Option 1: Install All Dependencies at Once

```bash
npm run install:all
```

This will:
1. Install root dependencies
2. Install frontend dependencies
3. Install backend Python dependencies

### Option 2: Manual Installation

**Frontend:**
```bash
cd frontend
npm install
```

**Backend:**
```bash
cd backend
pip install -r requirements.txt
```

## Development

### Run Both Frontend & Backend

```bash
npm run dev
```

This starts:
- **Frontend**: http://localhost:5173 (Vite dev server)
- **Backend**: http://localhost:8000 (FastAPI server)

### Run Frontend Only

```bash
npm run dev:frontend
```

Frontend will be available at `http://localhost:5173`

### Run Backend Only

```bash
npm run dev:backend
```

Backend API will be available at `http://localhost:8000`

### API Documentation

Once the backend is running, view the interactive API docs at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health Check
- `GET /api/health` - Check backend status

### Media Analysis
- `POST /api/analyze_video` - Analyze video file for deepfakes
- `POST /api/frame_analysis` - Analyze specific frame(s)
- `POST /api/media_risk_score` - Calculate risk score for media file

## Frontend Configuration

The frontend connects to the backend via environment variables:

**Development (.env.local in frontend/):**
```
VITE_API_URL=http://localhost:8000
```

**Production (.env.production):**
```
VITE_API_URL=https://api.technoax.com
```

## Backend CORS Configuration

The backend is configured to accept requests from:
- `http://localhost:5173` (Vite default)
- `http://localhost:8080` (Alternative port)
- `http://127.0.0.1:5173`
- `http://127.0.0.1:8080`

Update `backend/main.py` if you need to add more origins.

## Available npm Scripts

```bash
# Development
npm run dev              # Run both frontend and backend
npm run dev:frontend     # Frontend only (http://localhost:5173)
npm run dev:backend      # Backend only (http://localhost:8000)

# Building
npm run build            # Build frontend for production
npm run build:frontend   # Frontend build only
npm run build:backend    # Backend (no build needed)

# Code Quality
npm run lint             # Lint frontend code
npm run format           # Format frontend code

# Installation
npm run install:all      # Install all dependencies
```

## File Upload Integration

### From Frontend to Backend

The frontend API client (`frontend/src/lib/api/client.ts`) provides:

```typescript
import { analyzeVideo, analyzeFrame, calculateRiskScore } from '@/lib/api/client';

// Analyze a video file
const result = await analyzeVideo(videoFile);

// Analyze a frame from a video
const frameResult = await analyzeFrame(videoFile, frameIndex);

// Calculate risk score
const riskScore = await calculateRiskScore(mediaFile);
```

### Supported File Types

Check backend API documentation for supported formats. Typically:
- **Video**: MP4, MOV, AVI, etc.
- **Image**: JPG, PNG, etc.

## Environment Variables

### Root `.env`
- `VITE_API_URL` - Frontend API URL (default: http://localhost:8000)
- `BACKEND_PORT` - Backend port (default: 8000)
- `CORS_ORIGINS` - Comma-separated list of allowed origins

### Backend `.env`
Add any backend-specific configurations (API keys, model paths, etc.)

## Troubleshooting

### CORS Errors

If you get CORS errors, ensure:
1. Backend is running on the correct port (8000)
2. Frontend is on http://localhost:5173 or http://localhost:8080
3. Frontend URL is in the CORS allowed origins in `backend/main.py`

### Backend Connection Issues

1. Verify backend is running: `curl http://localhost:8000/api/health`
2. Check firewall settings
3. Ensure Python dependencies are installed: `pip install -r backend/requirements.txt`

### Node Modules Issues

Clear and reinstall:
```bash
cd frontend
rm -r node_modules package-lock.json
npm install
```

## Building for Production

### Frontend Build
```bash
npm run build:frontend
```

Outputs to `frontend/dist/`

### Backend Deployment

For production, run the backend with:
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

Or use Docker/other deployment tools.

## Documentation

- **Frontend**: See `frontend/README.md`
- **Backend**: See `backend/README.md`

## Support

For issues, check:
1. Backend logs in terminal
2. Browser DevTools console
3. API documentation at http://localhost:8000/docs

---

**Happy developing! 🚀**
