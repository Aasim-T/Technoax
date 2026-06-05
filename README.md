<div align="center">

<img src="https://img.shields.io/badge/Technoax-AI%20Trust%20Platform-6366f1?style=for-the-badge&logoColor=white" alt="Technoax" />

# 🛡️ Technoax — Explainable Digital Trust Platform

**AI-powered detection of deepfakes, manipulation, and synthetic media.**  
Analyze video, audio, and text for authenticity — with full explainability.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![TanStack](https://img.shields.io/badge/TanStack_Start-1.x-FF4154?style=flat-square&logo=reactquery&logoColor=white)](https://tanstack.com/start)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash-4285F4?style=flat-square&logo=google&logoColor=white)](https://aistudio.google.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

---

## ✨ Overview

**Technoax** is a full-stack AI platform for detecting and explaining digital content manipulation. It combines computer vision, natural language processing, and audio analysis to give a unified **Trust Score** for any piece of media.

Whether it's a suspicious video, a fear-mongering article, or a cloned voice recording — Technoax tells you **what's wrong, why it's flagged, and how confident it is**.

### Key Capabilities

| Capability | Description |
|---|---|
| 🎬 **Video Deepfake Detection** | Frame-by-frame analysis using OpenCV + Gemini Vision to detect visual manipulations |
| 📝 **Text Manipulation Analysis** | Detects emotional manipulation, fear tactics, urgency cues, clickbait & conspiracy framing |
| 🎙️ **Audio Authenticity Intelligence** | Transcribes and analyzes audio for synthetic voice signatures via Faster-Whisper + Librosa |
| 🔍 **Explainable AI** | Word-level matches, manipulation heatmaps, and Gemini-powered natural language explanations |
| 📊 **Risk Scoring** | Composite trust score + risk level with confidence intervals |
| 📈 **Analytics Dashboard** | Aggregated analysis trends and detection statistics |

---

## 🏗️ Architecture

```
technoax/
├── frontend/                  # React 19 + TanStack Start (TypeScript)
│   ├── src/
│   │   ├── components/        # shadcn/ui components + custom UI
│   │   ├── routes/            # File-based routing
│   │   │   ├── index.tsx      # Landing page
│   │   │   ├── text-analysis.tsx  # Text analysis tool
│   │   │   ├── dashboard.tsx  # Analytics dashboard
│   │   │   └── features.tsx   # Features showcase
│   │   ├── services/          # API client services
│   │   ├── hooks/             # Custom React hooks
│   │   └── types/             # TypeScript type definitions
│   └── vite.config.ts
│
├── backend-text/              # FastAPI — Text & Audio Analysis (Port 8000)
│   ├── main.py                # App factory with lifespan management
│   ├── routes/
│   │   ├── analyze.py         # Core text analysis endpoint
│   │   ├── enhanced_analyze.py  # Gemini-powered deep analysis
│   │   ├── audio_routes.py    # Audio upload & transcription
│   │   └── analytics.py       # Aggregated analytics
│   ├── services/              # NLP & AI scoring logic
│   ├── models/                # Pydantic data models
│   ├── schemas/               # Request/response schemas
│   └── config/                # Settings & env management
│
├── backend-video/             # FastAPI — Video/Frame Analysis (Port 8001)
│   ├── main.py
│   ├── api/
│   │   ├── analyze_video.py   # Video deepfake analysis
│   │   ├── frame_analysis.py  # Single frame inspection
│   │   └── media_risk_score.py  # Media risk scoring
│   ├── services/              # Vision model integrations
│   └── utils/                 # Frame extraction, preprocessing
│
└── package.json               # Root orchestrator (runs all 3 services)
```

---

## 🚀 Quick Start

### Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| **Node.js** | 18+ | Frontend & monorepo scripts |
| **Python** | 3.8+ | Backend services |
| **npm** | 8+ | Package management |
| **pip** | Latest | Python dependencies |

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/technoax.git
cd technoax
```

### 2. Configure Environment Variables

**Backend Text** (`backend-text/.env`):
```env
# Get your API key: https://aistudio.google.com/apikey
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
APP_NAME=Technoax
APP_VERSION=1.0.0
DEBUG=false
CORS_ORIGINS=*
```

**Backend Video** (`backend-video/.env`):
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

**Frontend** (`frontend/.env`):
```env
VITE_API_TEXT_URL=http://localhost:8000
VITE_API_VIDEO_URL=http://localhost:8001
```

### 3. Install All Dependencies

```bash
npm run install:all
```

This installs frontend Node modules + all Python packages for both backends.

### 4. Start Development Servers

```bash
npm run dev
```

This concurrently launches all three services:

| Service | URL | Description |
|---|---|---|
| 🖥️ Frontend | http://localhost:5173 | React + Vite dev server |
| 📝 Text API | http://localhost:8000 | Text & audio analysis |
| 🎬 Video API | http://localhost:8001 | Video & frame analysis |

---

## 📡 API Reference

### Text & Audio Analysis (`localhost:8000`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health probe |
| `POST` | `/analyze` | Basic text manipulation analysis |
| `POST` | `/enhanced-analyze` | Gemini-powered deep analysis with AI explanations |
| `POST` | `/audio` | Upload & analyze audio file for synthetic voice detection |
| `GET` | `/analytics` | Aggregated detection statistics |

**Example — Analyze Text:**
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "URGENT! Act now before it is too late! They do not want you to know this!"}'
```

**Response:**
```json
{
  "trust_score": 23.5,
  "risk_level": "HIGH",
  "manipulation_types": ["urgency", "fear_tactic", "conspiracy_framing"],
  "word_matches": [...],
  "heatmap_indices": [0, 1, 5, 12],
  "explanation": "This text exhibits multiple high-confidence manipulation patterns..."
}
```

---

### Video & Frame Analysis (`localhost:8001`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health probe |
| `POST` | `/api/analyze_video` | Upload & analyze video for deepfake artifacts |
| `POST` | `/api/frame_analysis` | Analyze a specific extracted frame |
| `POST` | `/api/media_risk_score` | Calculate composite risk score for media file |

**Interactive API Docs:**
- Text API: http://localhost:8000/docs (Swagger) | http://localhost:8000/redoc
- Video API: http://localhost:8001/docs (Swagger) | http://localhost:8001/redoc

---

## 🛠️ Tech Stack

### Frontend
| Technology | Version | Role |
|---|---|---|
| **React** | 19 | UI framework |
| **TanStack Start** | 1.x | Full-stack React framework with SSR |
| **TanStack Router** | 1.x | Type-safe file-based routing |
| **TanStack Query** | 5.x | Server state management |
| **Tailwind CSS** | 4.x | Utility-first styling |
| **shadcn/ui** | Latest | Accessible component library |
| **Radix UI** | 1.x | Headless UI primitives |
| **Framer Motion** | 12.x | Animations & transitions |
| **Recharts** | 2.x | Data visualization |
| **Lucide React** | Latest | Icon library |
| **Zod** | 3.x | Schema validation |
| **React Hook Form** | 7.x | Form management |

### Backend (Text & Audio)
| Technology | Version | Role |
|---|---|---|
| **FastAPI** | 0.115+ | API framework |
| **Pydantic** | 2.9+ | Data validation & settings |
| **Google Gemini** (`google-genai`) | 1.0+ | AI analysis & explainability |
| **Faster-Whisper** | 1.0+ | Offline speech-to-text |
| **Librosa** | 0.10+ | Audio feature extraction |
| **SoundFile** | 0.12+ | Audio I/O |
| **Uvicorn** | 0.32+ | ASGI server |

### Backend (Video)
| Technology | Version | Role |
|---|---|---|
| **FastAPI** | Latest | API framework |
| **OpenCV** | Latest | Computer vision & frame extraction |
| **NumPy** | Latest | Numerical processing |
| **Google Gemini** (`google-genai`) | Latest | Vision-based deepfake analysis |

---

## 📜 Available Scripts

```bash
# ── Development ────────────────────────────────────────────────────────────────
npm run dev               # Start all 3 services concurrently
npm run dev:frontend      # Frontend only  →  http://localhost:5173
npm run dev:backend-text  # Text API only  →  http://localhost:8000
npm run dev:backend-video # Video API only →  http://localhost:8001

# ── Build ───────────────────────────────────────────────────────────────────────
npm run build             # Build frontend for production
npm run build:frontend    # Frontend build only (outputs to frontend/dist/)

# ── Code Quality ────────────────────────────────────────────────────────────────
npm run lint              # ESLint on frontend
npm run format            # Prettier format on frontend

# ── Installation ────────────────────────────────────────────────────────────────
npm run install:all       # Install all Node + Python dependencies at once
```

---

## 🔧 Supported Media Formats

| Type | Formats |
|---|---|
| **Video** | MP4, MOV, AVI, MKV, WebM |
| **Audio** | MP3, WAV, OGG, FLAC, M4A |
| **Image / Frame** | JPG, PNG, WebP |
| **Text** | Plain text, JSON body |

---

## ⚙️ Configuration

### CORS

The backends accept requests from all origins by default (`CORS_ORIGINS=*`).  
For production, restrict to your domain in `backend-text/.env`:

```env
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

### Gemini Model

Switch between Gemini models in `backend-text/.env`:

```env
GEMINI_MODEL=gemini-2.5-flash    # Fast, cost-efficient (default)
GEMINI_MODEL=gemini-2.5-pro      # Deeper reasoning, more expensive
```

> **Note:** If `GEMINI_API_KEY` is not set, the platform falls back to **rule-based analysis only** — no AI explanations, but core detection still works.

---

## 🚢 Production Deployment

### Frontend

```bash
npm run build:frontend
# Outputs to frontend/dist/ — serve with any static host (Vercel, Netlify, Nginx)
```

### Backend (Production)

```bash
# Text Analysis API
cd backend-text
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Video Analysis API
cd backend-video
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 2
```

> For GPU-accelerated video analysis, use `--workers 1` with async queue workers.

---

## 🐛 Troubleshooting

<details>
<summary><strong>CORS Errors in Browser</strong></summary>

1. Ensure the correct backend is running on the expected port
2. Verify the frontend `.env` has the right API URLs
3. Set `CORS_ORIGINS=*` in both backend `.env` files during development

</details>

<details>
<summary><strong>Gemini API Not Working</strong></summary>

1. Confirm `GEMINI_API_KEY` is set in `backend-text/.env`
2. Get a free key at: https://aistudio.google.com/apikey
3. Use only `google-genai` — do **not** install `google-generativeai` (deprecated)

</details>

<details>
<summary><strong>Python Dependency Conflicts</strong></summary>

Use a virtual environment:
```bash
cd backend-text
python -m venv venv
venv\Scripts\activate       # Windows
source venv/bin/activate    # macOS/Linux
pip install -r requirements.txt
```

</details>

<details>
<summary><strong>Frontend Node Module Issues</strong></summary>

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

</details>

<details>
<summary><strong>Port Already in Use</strong></summary>

Kill the process on the port:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:8000 | xargs kill -9
```

</details>

---

## 📁 Key Files Reference

| File | Purpose |
|---|---|
| [`package.json`](package.json) | Root monorepo orchestrator & dev scripts |
| [`frontend/src/routes/index.tsx`](frontend/src/routes/index.tsx) | Landing page |
| [`frontend/src/routes/text-analysis.tsx`](frontend/src/routes/text-analysis.tsx) | Text analysis UI |
| [`frontend/src/routes/dashboard.tsx`](frontend/src/routes/dashboard.tsx) | Analytics dashboard |
| [`backend-text/main.py`](backend-text/main.py) | Text API app factory |
| [`backend-text/routes/enhanced_analyze.py`](backend-text/routes/enhanced_analyze.py) | Gemini deep analysis |
| [`backend-text/routes/audio_routes.py`](backend-text/routes/audio_routes.py) | Audio analysis routes |
| [`backend-video/main.py`](backend-video/main.py) | Video API entry point |
| [`backend-video/api/analyze_video.py`](backend-video/api/analyze_video.py) | Video deepfake detection |

---

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/your-feature-name`
3. **Commit** your changes: `git commit -m 'feat: add your feature'`
4. **Push** to the branch: `git push origin feature/your-feature-name`
5. **Open** a Pull Request

Please follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with using FastAPI, React, and Google Gemini**

*Technoax — Trust, but verify.*

</div>
