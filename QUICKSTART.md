# Quick Start Guide - Technoax Full Stack

## Project Successfully Merged! ✅

Your Technoax project now has both frontend and backend integrated in a monorepo structure.

## 📁 Location

```
C:\Users\Administrator\Downloads\technoax-fullstack\
```

## 🚀 Quick Start

### 1. Install All Dependencies

```bash
cd C:\Users\Administrator\Downloads\technoax-fullstack
npm run install:all
```

This will install:
- Frontend dependencies (485 packages)
- Backend dependencies (FastAPI, OpenCV, etc.)

### 2. Start Development Environment

```bash
npm run dev
```

This runs:
- **Frontend**: http://localhost:5173 (React with Vite)
- **Backend**: http://localhost:8000 (FastAPI)

### 3. Access the Application

- **Web App**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **Backend Health**: http://localhost:8000/api/health

## 📚 What's Where

| Component | Location | Port |
|-----------|----------|------|
| Frontend (React) | `./frontend/` | 5173 |
| Backend (FastAPI) | `./backend/` | 8000 |
| API Client | `./frontend/src/lib/api/client.ts` | - |
| Shared Config | `./.env` | - |

## 🔧 Common Tasks

```bash
# Run only frontend
npm run dev:frontend

# Run only backend  
npm run dev:backend

# Build frontend
npm run build:frontend

# Lint/format code
npm run lint
npm run format
```

## 🌐 API Integration

The frontend is pre-configured to connect to the backend:

```typescript
// Example usage in frontend
import { analyzeVideo } from '@/lib/api/client';

const result = await analyzeVideo(videoFile);
console.log(`Risk Score: ${result.risk_score}`);
```

## 🛠️ Configuration

### Frontend `.env.local`
```
VITE_API_URL=http://localhost:8000
```

### Backend CORS
Already configured for localhost development in `backend/main.py`

## 📝 File Structure

```
technoax-fullstack/
├── frontend/               # React/TanStack frontend
│   ├── src/
│   │   ├── components/    # UI components
│   │   ├── routes/        # Page routes
│   │   └── lib/api/       # API client ← Uses backend
│   └── .env.local
├── backend/                # FastAPI backend
│   ├── api/               # Route handlers
│   ├── models/            # ML models
│   ├── services/          # Business logic
│   ├── main.py           # Entry point (CORS enabled)
│   └── requirements.txt
├── package.json           # Root npm config
├── .env                   # Shared environment
└── README.md              # Full documentation
```

## 🔌 API Endpoints Available

- `GET /api/health` - System health check
- `POST /api/analyze_video` - Analyze video file
- `POST /api/frame_analysis` - Analyze specific frame
- `POST /api/media_risk_score` - Calculate risk score

See http://localhost:8000/docs for full interactive documentation.

## ✅ Next Steps

1. **Install dependencies**: `npm run install:all`
2. **Start dev environment**: `npm run dev`
3. **Open browser**: http://localhost:5173
4. **Check API docs**: http://localhost:8000/docs
5. **Start building**: Modify frontend/backend code and watch HMR reload!

## 💡 Tips

- Both servers have hot reload enabled
- Frontend changes auto-refresh in browser
- Backend changes auto-restart the server
- API responses are logged in browser console
- Backend logs appear in your terminal

## 🐛 Need Help?

Check the full [README.md](./README.md) for troubleshooting and detailed documentation.

---

**Happy building! 🎉**
