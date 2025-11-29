# Local Setup Guide - DocuHelp API Integration

This guide explains how to set up and run the DocuHelp application locally with Firebase backend integration.

## Prerequisites

- Python 3.8+
- Node.js 14+
- Firebase account and project
- Firebase Admin SDK credentials

## Backend Setup (Python/FastAPI)

### 1. Environment Configuration

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Firebase Configuration
FIREBASE_CREDENTIALS=./firebase-credentials.json
FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=True

# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Upload Settings
MAX_UPLOAD_SIZE=500000000
UPLOAD_DIR=uploads/videos

# Logging
LOG_LEVEL=INFO
```

### 2. Firebase Credentials

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Go to **Project Settings > Service Accounts**
4. Click **Generate New Private Key**
5. Save the JSON file as `firebase-credentials.json` in the project root

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
# or
pip install fastapi uvicorn python-multipart firebase-admin
```

### 4. Run the Backend Server

```bash
# From project root
python -m uvicorn src.docuhelp.ui.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Or run directly:

```bash
python src/docuhelp/ui/api/main.py
```

The API will be available at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

## Frontend Setup (React)

### 1. Navigate to Frontend Directory

```bash
cd frontend
```

### 2. Environment Configuration

Create a `.env` file in the `frontend` directory:

```bash
cp .env.example .env
```

Edit `frontend/.env`:

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_FIREBASE_API_KEY=your-api-key
REACT_APP_FIREBASE_PROJECT_ID=your-project-id
REACT_APP_FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
```

### 3. Install Dependencies

```bash
npm install
```

### 4. Run the Frontend

```bash
npm start
```

The app will open at: `http://localhost:3000`

## Usage Flow

1. **Start Backend**: Run the FastAPI server on port 8000
2. **Start Frontend**: Run the React app on port 3000
3. **Select Procedure**: Choose a surgical procedure from the list
4. **Upload Files**:
   - Video file (MP4, required)
   - SOP document (PDF/DOC, optional)
5. **API Upload**: Files are uploaded to:
   - `POST /api/v1/video/upload`
   - Saved locally in `uploads/videos/`
   - Uploaded to Firebase Storage
   - Metadata stored in Firestore

## API Endpoints

### Upload Video
```
POST /api/v1/video/upload
Content-Type: multipart/form-data

Form Data:
- video: file (required)
- procedure: string (required)
- sop_file: file (optional)

Response:
{
  "success": true,
  "video_id": "uuid",
  "procedure": "Laparoscopic Cholecystectomy",
  "video_url": "https://...",
  "sop_url": "https://...",
  "local_path": "uploads/videos/..."
}
```

### Get Video Metadata
```
GET /api/v1/video/video/{video_id}

Response:
{
  "video_id": "uuid",
  "procedure": "Laparoscopic Cholecystectomy",
  "video_filename": "surgery.mp4",
  "video_url": "https://...",
  "status": "uploaded",
  "processed": false
}
```

### Get Video Status
```
GET /api/v1/video/video/{video_id}/status

Response:
{
  "video_id": "uuid",
  "status": "uploaded",
  "processed": false,
  "procedure": "Laparoscopic Cholecystectomy"
}
```

## Troubleshooting

### CORS Errors
- Ensure `ALLOWED_ORIGINS` in backend `.env` includes frontend URL
- Check that both servers are running

### Firebase Authentication Errors
- Verify `firebase-credentials.json` path is correct
- Check Firebase project permissions
- Ensure Storage bucket is created in Firebase Console

### Upload Failures
- Check file size limits (default 500MB)
- Verify `uploads/videos/` directory exists and is writable
- Check Firebase Storage rules

### Port Already in Use
```bash
# Kill process on port 8000
# Linux/Mac:
lsof -ti:8000 | xargs kill -9

# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

## Next Steps

The uploaded video is now ready for VLM (Vision Language Model) inference. The video metadata includes:
- Local file path for processing
- Firebase Storage URL for frontend display
- Procedure category for context
- Firestore document for status tracking

You can now integrate VLM processing in a separate step that reads from:
- `local_path`: for local file processing
- `video_id`: for tracking in Firestore
- `procedure`: for procedure-specific inference
