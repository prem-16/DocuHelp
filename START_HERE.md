# 🚀 Start Here - Local Setup (No Firebase)

## You're Ready to Go!

Your application is configured for **local hosting only** - no Firebase setup required.

## Quick Start

### 1. Install Dependencies (First Time Only)

```bash
# Backend (includes OpenCV for VLM)
pip install -e .

# Frontend
cd frontend
npm install
cd ..
```

### 2. Configure OpenRouter API Key

For VLM (AI video analysis), add your OpenRouter API key to `.env`:

```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

Get a free key at https://openrouter.ai/ (see [VLM_QUICK_START.md](VLM_QUICK_START.md))

### 3. Run the Application

**Terminal 1 - Backend:**
```bash
python -m uvicorn src.docuhelp.ui.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

Then open: **http://localhost:3000**

## What Happens Automatically

1. **Select a Procedure** - Choose from surgical procedures
2. **Upload Video** - Drag & drop your MP4 file
3. **Automatic AI Analysis** - VLM processes video in background!
   - Extracts frames (1 per second)
   - Sends to Gemini 2.0 Flash via OpenRouter
   - Identifies surgical phases with timestamps
   - Returns key frames and descriptions

## Where Files Go

- **Videos**: `uploads/videos/`
- **Metadata**: `uploads/metadata/` (includes VLM results)
- **No cloud** - Everything stays local

## Check VLM Results

```bash
# Get video analysis results
curl http://localhost:8000/api/v1/video/video/{video_id}/vlm-results
```

## API Endpoints

- **Upload** (starts VLM): `POST /api/v1/video/upload`
- **VLM Results**: `GET /api/v1/video/video/{video_id}/vlm-results`
- **VLM Status**: `GET /api/v1/video/video/{video_id}/status`
- **Key Frames**: `GET /api/v1/video/video/{video_id}/phase/{index}/frame`
- **API Docs**: http://localhost:8000/docs

## Example: Get VLM Results

```python
import requests

# Upload video
files = {
    'video': open('surgery.mp4', 'rb'),
    'procedure': (None, 'Laparoscopic Cholecystectomy')
}
response = requests.post('http://localhost:8000/api/v1/video/upload', files=files)
video_id = response.json()['video_id']

# Wait for processing (or poll status endpoint)
import time
time.sleep(30)

# Get results
results = requests.get(f'http://localhost:8000/api/v1/video/video/{video_id}/vlm-results')
phases = results.json()['phases']

for phase in phases:
    print(f"{phase['timestamp_range']}: {phase['description']}")
```

## Need Help?

- **VLM Setup**: See [VLM_QUICK_START.md](VLM_QUICK_START.md) for AI video analysis
- **VLM API**: See [VLM_PIPELINE_GUIDE.md](VLM_PIPELINE_GUIDE.md) for detailed docs
- **Quick Start**: See [QUICK_START.md](QUICK_START.md)
- **Local Setup**: See [LOCAL_SETUP.md](LOCAL_SETUP.md)

## Want Firebase Later?

Just set `USE_FIREBASE=true` in `.env` and add credentials. The system supports both!

---

**Ready to analyze surgical videos with AI!** 🎥🤖✅
