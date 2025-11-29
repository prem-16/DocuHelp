# Quick Start Guide

## Choose Your Setup

### 🚀 Local-Only Setup (Recommended - No Firebase)
See **[LOCAL_SETUP.md](LOCAL_SETUP.md)** for simple local hosting without Firebase.

### ☁️ Firebase Setup (Optional)
Follow this guide if you want to use Firebase Storage and Firestore.

---

## Local-Only Setup (No Firebase)

### 1. Configure Environment

```bash
# Copy environment template (already configured for local mode)
cp .env.example .env
```

**That's it!** The default settings use local storage only.

### 2. Install Dependencies

**Backend:**
```bash
pip install -e .
```

**Frontend:**
```bash
cd frontend
npm install
cd ..
```

## Running the Application

### Option 1: Two Terminal Windows

**Terminal 1 - Backend:**
```bash
python -m uvicorn src.docuhelp.ui.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

### Option 2: Single Command (if you have concurrently)
```bash
npm install -g concurrently
concurrently "python -m uvicorn src.docuhelp.ui.api.main:app --reload" "cd frontend && npm start"
```

## Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Test the Upload

1. Open http://localhost:3000
2. Select a surgical procedure
3. Upload a video file (MP4 recommended)
4. Optionally upload SOP document
5. Click "Upload & Continue"
6. Check the console for success message

## Verify Upload

**Check Local Files:**
```bash
# Windows
dir uploads\videos
dir uploads\metadata

# Linux/Mac
ls uploads/videos/
ls uploads/metadata/
```

**Check API Response:**
Open browser DevTools (F12) → Network → Check the upload response

**Check Console:**
Backend console should show: `"storage_mode": "local"`

## Common Commands

**Stop Servers:**
- Press `Ctrl+C` in each terminal

**Clear Uploads:**
```bash
# Windows
rmdir /s /q uploads\videos
mkdir uploads\videos

# Linux/Mac
rm -rf uploads/videos/*
```

**View API Endpoints:**
Open http://localhost:8000/docs

**Check Backend Logs:**
Look at the terminal running uvicorn

## Environment Variables

### Backend (.env) - Local Mode
```env
USE_FIREBASE=false
API_PORT=8000
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

### Frontend (frontend/.env)
```env
REACT_APP_API_URL=http://localhost:8000
```

---

## Optional: Enable Firebase

If you want to use Firebase Storage instead of local storage:

1. Set `USE_FIREBASE=true` in `.env`
2. Download `firebase-credentials.json` from Firebase Console
3. Add to `.env`: `FIREBASE_CREDENTIALS=./firebase-credentials.json`
4. Restart backend server

See [LOCAL_SETUP_GUIDE.md](LOCAL_SETUP_GUIDE.md) for Firebase setup details.

## Need Help?

- See [LOCAL_SETUP_GUIDE.md](LOCAL_SETUP_GUIDE.md) for detailed setup
- See [API_INTEGRATION_SUMMARY.md](API_INTEGRATION_SUMMARY.md) for architecture details
- Check backend logs for error messages
- Open browser DevTools (F12) for frontend errors
