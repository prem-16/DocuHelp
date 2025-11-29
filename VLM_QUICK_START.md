# VLM Quick Start - Automatic Video Analysis

Get your surgical video analyzed by AI in 3 steps!

## Prerequisites

- Backend and frontend running (see [START_HERE.md](START_HERE.md))
- OpenRouter API key

## Step 1: Get OpenRouter API Key (2 minutes)

1. Go to https://openrouter.ai/
2. Sign up (free tier available)
3. Go to **API Keys** → **Create Key**
4. Copy your key (starts with `sk-or-v1-...`)

## Step 2: Add API Key to Environment

Edit your `.env` file:

```env
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
```

**Restart the backend** to load the new key:
```bash
# Stop with Ctrl+C, then restart:
python -m uvicorn src.docuhelp.ui.api.main:app --host 0.0.0.0 --port 8000 --reload
```

## Step 3: Upload & Get Results!

### Upload via Frontend

1. Open http://localhost:3000
2. Select procedure (e.g., "Laparoscopic Cholecystectomy")
3. Upload your MP4 video
4. Click **"Upload & Continue"**
5. VLM processing starts **automatically**!

### Check Results

**Option 1: API (Quick)**

```bash
# Replace {video_id} with your video ID from upload response
curl http://localhost:8000/api/v1/video/video/{video_id}/vlm-results
```

**Option 2: Python Script**

```python
import requests
import time

video_id = "your-video-id-here"

# Poll for results
while True:
    r = requests.get(f'http://localhost:8000/api/v1/video/video/{video_id}/vlm-results')

    if r.status_code == 200:
        results = r.json()
        print(f"\n✅ Analysis Complete!")
        print(f"Found {len(results['phases'])} phases:\n")

        for i, phase in enumerate(results['phases'], 1):
            print(f"{i}. {phase['timestamp_range']}: {phase['description']}")

        break
    else:
        print("Still processing...")
        time.sleep(5)
```

## What You Get

VLM analysis returns:

```json
{
  "procedure": "Laparoscopic Cholecystectomy",
  "status": "completed",
  "vlm_summary": "Detailed text summary...",
  "phases": [
    {
      "timestamp_range": "0:00-0:45",
      "key_timestamp": "0:23",
      "description": "Initial trocar insertion and camera positioning",
      "has_key_frame": true
    },
    {
      "timestamp_range": "0:45-2:30",
      "key_timestamp": "1:38",
      "description": "Dissection of gallbladder from liver bed",
      "has_key_frame": true
    }
  ],
  "vlm_latency": 25.4
}
```

## Get Key Frame Images

Each phase has a key frame (screenshot):

```bash
# Get frame for phase 0 (first phase)
curl http://localhost:8000/api/v1/video/video/{video_id}/phase/0/frame
```

Returns base64 image you can display in frontend!

## Processing Time

- **Short video** (1-2 min): ~20-30 seconds
- **Medium video** (5-10 min): ~40-60 seconds
- **Long video** (20+ min): ~2-3 minutes

VLM processes in the background - you get results when done!

## Troubleshooting

### "OpenRouter API key not found"

Check your `.env` file:
```bash
cat .env | grep OPENROUTER
```

Make sure it's set and restart backend.

### "ModuleNotFoundError: opencv-python"

Install dependencies:
```bash
pip install opencv-python
# or
pip install -e .
```

### VLM Never Completes

Check backend logs for errors:
```bash
# Look for errors in the terminal running uvicorn
# Should see: "VLM processing completed for {video_id}: X phases found"
```

Check status:
```bash
curl http://localhost:8000/api/v1/video/video/{video_id}/status
```

If status is "error", check metadata file:
```bash
cat uploads/metadata/{video_id}.json
```

## Next Steps

- See [VLM_PIPELINE_GUIDE.md](VLM_PIPELINE_GUIDE.md) for full API documentation
- Integrate results into your frontend
- Customize VLM prompts for specific procedures

---

**Ready to analyze surgical videos with AI!** 🎥🤖
