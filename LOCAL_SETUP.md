# Local Setup Guide - No Firebase Required

Simple guide to run DocuHelp locally without any Firebase configuration.

## Quick Setup (5 Minutes)

### 1. Copy Environment File

```bash
cp .env.example .env
```

**That's it!** The default `.env` file is already configured for local-only mode.

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

### 3. Run the Application

**Terminal 1 - Start Backend:**
```bash
python -m uvicorn src.docuhelp.ui.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Start Frontend:**
```bash
cd frontend
npm start
```

### 4. Open Application

Open your browser to: **http://localhost:3000**

## How It Works

### Local Storage

- **Video files**: Saved to `uploads/videos/`
- **Metadata**: Saved to `uploads/metadata/` as JSON files
- **No cloud required**: Everything stays on your machine

### Workflow

1. Select a surgical procedure
2. Upload your MP4 video file (+ optional SOP document)
3. Files are saved locally
4. Metadata stored in JSON format
5. Video ready for VLM processing

## File Structure

After uploading a video, you'll see:

```
uploads/
├── videos/
│   ├── {uuid}_surgery-video.mp4     # Your video file
│   └── {uuid}_sop-document.pdf      # Optional SOP file
└── metadata/
    └── {uuid}.json                   # Video metadata
```

### Example Metadata File

```json
{
  "video_id": "550e8400-e29b-41d4-a716-446655440000",
  "procedure": "Laparoscopic Cholecystectomy",
  "video_filename": "surgery-video.mp4",
  "local_path": "uploads/videos/550e8400_surgery-video.mp4",
  "sop_filename": "sop-document.pdf",
  "sop_local_path": "uploads/videos/550e8400_sop-document.pdf",
  "status": "uploaded",
  "uploaded_at": "2025-11-29T10:30:00Z",
  "processed": false
}
```

## API Endpoints

All endpoints work locally without Firebase:

### Upload Video
```bash
POST http://localhost:8000/api/v1/video/upload
```

### Get Video Metadata
```bash
GET http://localhost:8000/api/v1/video/video/{video_id}
```

### Check Video Status
```bash
GET http://localhost:8000/api/v1/video/video/{video_id}/status
```

### API Documentation
```bash
http://localhost:8000/docs
```

## VLM Integration

Access uploaded videos for VLM processing:

```python
from docuhelp.ui.local_storage import get_metadata

# Get video data
metadata = get_metadata(video_id)
video_path = metadata["local_path"]       # Path to MP4 file
procedure = metadata["procedure"]          # Surgical procedure category

# Process with your VLM
# your_vlm.process(video_path, procedure)
```

## Troubleshooting

### Port Already in Use

**Backend (8000):**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

**Frontend (3000):**
```bash
# Stop the npm process with Ctrl+C
# Or set a different port in frontend/package.json
```

### Upload Directory Not Found

The directories are created automatically, but if you get errors:

```bash
mkdir -p uploads/videos
mkdir -p uploads/metadata
```

### CORS Errors

Make sure both servers are running and the `.env` file has:
```env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

### Module Not Found

Reinstall dependencies:
```bash
pip install -e .
cd frontend && npm install
```

## Environment Variables

Your `.env` file should look like this:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=True

# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Upload Settings
UPLOAD_DIR=uploads/videos
MAX_UPLOAD_SIZE=500000000

# Logging
LOG_LEVEL=INFO

# Storage Backend (local by default)
USE_FIREBASE=false
```

## Success Checklist

- ✅ Backend running on http://localhost:8000
- ✅ Frontend running on http://localhost:3000
- ✅ Can select a procedure
- ✅ Can upload a video file
- ✅ Files appear in `uploads/videos/`
- ✅ Metadata files appear in `uploads/metadata/`
- ✅ Console shows "storage_mode": "local"

## Next Steps

1. **Test the Upload**: Try uploading a small video file
2. **Check the Files**: Look in `uploads/videos/` and `uploads/metadata/`
3. **Integrate VLM**: Use the local file paths for your VLM processing

## Optional: Enable Firebase Later

If you decide to use Firebase later:

1. Set `USE_FIREBASE=true` in `.env`
2. Download `firebase-credentials.json`
3. Add Firebase configuration to `.env`
4. Restart the backend

The system will automatically switch to Firebase storage while still keeping local copies.

---

**Status**: ✅ Local-Only Setup - No Firebase Required
**Storage**: Local files only
**Ready For**: VLM Integration
