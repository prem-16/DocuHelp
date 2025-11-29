# VLM Pipeline Guide

Complete guide for the automated VLM (Vision Language Model) inference pipeline using OpenRouter and Gemini 2.0 Flash.

## Overview

The VLM pipeline automatically:
1. Extracts frames from uploaded MP4 videos (1 frame per second)
2. Sends frames to OpenRouter's Gemini 2.0 Flash model
3. Analyzes surgical procedures with procedure-specific context
4. Extracts timestamped phases and key frames
5. Stores results for frontend display

## Setup

### 1. Install Dependencies

```bash
pip install -e .
```

This installs:
- `opencv-python` - Video frame extraction
- `openai` - OpenRouter API client (already installed)
- `python-dotenv` - Environment configuration

### 2. Get OpenRouter API Key

1. Go to https://openrouter.ai/
2. Sign up or log in
3. Navigate to API Keys
4. Create a new API key
5. Copy the key (starts with `sk-or-v1-...`)

### 3. Configure Environment

Add to your `.env` file:

```env
OPENROUTER_API_KEY=sk-or-v1-your-actual-api-key-here
```

## How It Works

### Automatic Processing Flow

```
User uploads video
    ↓
Video saved to uploads/videos/
    ↓
Metadata saved to uploads/metadata/
    ↓
Background task starts automatically
    ↓
Extract frames (1 fps) → Base64 encoding
    ↓
Send to OpenRouter Gemini 2.0 Flash
    ↓
Parse response → Extract phases & timestamps
    ↓
Save results to metadata JSON
    ↓
Status: completed
```

### Processing Timeline

1. **Upload** (0-5s) - Video file upload
2. **Frame Extraction** (varies) - 1 frame/sec extraction
3. **VLM Inference** (10-60s) - OpenRouter API call
4. **Post-processing** (1-2s) - Parse results, save metadata

**Total**: ~20-70 seconds depending on video length

## API Endpoints

### 1. Upload Video (Triggers VLM)

```http
POST /api/v1/video/upload
Content-Type: multipart/form-data

Form fields:
- video: MP4 file
- procedure: Surgical procedure name
- sop_file: (optional) SOP document
```

**Response:**
```json
{
  "success": true,
  "video_id": "abc-123",
  "procedure": "Laparoscopic Cholecystectomy",
  "message": "Video uploaded successfully. VLM processing started.",
  "vlm_status": "processing"
}
```

### 2. Check VLM Status

```http
GET /api/v1/video/video/{video_id}/status
```

**Response:**
```json
{
  "video_id": "abc-123",
  "status": "processing",  // or "completed", "error"
  "processed": false,
  "procedure": "Laparoscopic Cholecystectomy",
  "vlm_latency": null,
  "phases_count": 0
}
```

### 3. Get VLM Results

```http
GET /api/v1/video/video/{video_id}/vlm-results
```

**Response (Processing):**
```json
{
  "video_id": "abc-123",
  "status": "processing",
  "message": "VLM processing processing. Results not ready yet.",
  "processed": false
}
```

**Response (Completed):**
```json
{
  "video_id": "abc-123",
  "procedure": "Laparoscopic Cholecystectomy",
  "status": "completed",
  "processed": true,
  "vlm_summary": "Full text summary from VLM...",
  "phases": [
    {
      "timestamp_range": "0:00-0:45",
      "start_seconds": 0,
      "end_seconds": 45,
      "key_timestamp": "0:23",
      "key_timestamp_seconds": 23,
      "description": "Initial trocar insertion and camera positioning...",
      "has_key_frame": true
    },
    {
      "timestamp_range": "0:45-2:30",
      "start_seconds": 45,
      "end_seconds": 150,
      "key_timestamp": "1:38",
      "key_timestamp_seconds": 98,
      "description": "Dissection of the gallbladder from liver bed...",
      "has_key_frame": true
    }
  ],
  "vlm_latency": 25.4,
  "model": "google/gemini-2.0-flash-exp:free"
}
```

### 4. Get Key Frame Image

```http
GET /api/v1/video/video/{video_id}/phase/{phase_index}/frame
```

**Response:**
```json
{
  "video_id": "abc-123",
  "phase_index": 0,
  "timestamp": "0:23",
  "timestamp_range": "0:00-0:45",
  "description": "Initial trocar insertion...",
  "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

## VLM Prompt Template

The system uses this prompt for Gemini:

```
This is a {procedure} surgical procedure video.

Analyze this surgical video and provide a detailed summary.

For each distinct phase or action in the video, provide:
1. **Timestamp Range**: Start and end time (e.g., "0:00-0:45")
2. **Description**: Clear description of what is happening
3. **Key Timestamp**: A single timestamp within the range that best represents this phase

Format your response as a structured list of phases.

Consider the standard steps for {procedure} in your analysis.
```

## Code Examples

### Python: Trigger VLM Processing

```python
import requests

# Upload video (VLM starts automatically)
files = {
    'video': open('surgery.mp4', 'rb'),
    'procedure': (None, 'Laparoscopic Cholecystectomy')
}

response = requests.post(
    'http://localhost:8000/api/v1/video/upload',
    files=files
)

video_id = response.json()['video_id']
print(f"Video uploaded: {video_id}")
print("VLM processing started in background...")
```

### Python: Check Status & Get Results

```python
import requests
import time

def wait_for_vlm_results(video_id, max_wait=120):
    """Poll for VLM results."""
    start = time.time()

    while time.time() - start < max_wait:
        # Check status
        status_resp = requests.get(
            f'http://localhost:8000/api/v1/video/video/{video_id}/status'
        )
        status = status_resp.json()

        if status['processed']:
            # Get full results
            results_resp = requests.get(
                f'http://localhost:8000/api/v1/video/video/{video_id}/vlm-results'
            )
            return results_resp.json()

        print(f"Status: {status['status']}, waiting...")
        time.sleep(5)

    raise TimeoutError("VLM processing timed out")

# Usage
results = wait_for_vlm_results(video_id)
print(f"Found {len(results['phases'])} phases")

for i, phase in enumerate(results['phases']):
    print(f"\nPhase {i+1}: {phase['timestamp_range']}")
    print(f"  {phase['description']}")
```

### JavaScript: Frontend Integration

```javascript
// Upload video
async function uploadVideo(videoFile, procedure) {
  const formData = new FormData();
  formData.append('video', videoFile);
  formData.append('procedure', procedure);

  const response = await fetch('http://localhost:8000/api/v1/video/upload', {
    method: 'POST',
    body: formData
  });

  const result = await response.json();
  return result.video_id;
}

// Poll for results
async function getVLMResults(videoId) {
  const response = await fetch(
    `http://localhost:8000/api/v1/video/video/${videoId}/vlm-results`
  );

  if (response.status === 202) {
    // Still processing
    return null;
  }

  return await response.json();
}

// Usage
const videoId = await uploadVideo(file, 'Laparoscopic Cholecystectomy');

// Poll every 5 seconds
const interval = setInterval(async () => {
  const results = await getVLMResults(videoId);

  if (results) {
    clearInterval(interval);
    console.log('VLM Results:', results);
    displayResults(results);
  }
}, 5000);
```

## File Structure

```
uploads/
├── videos/
│   └── {uuid}_surgery.mp4
└── metadata/
    └── {uuid}.json
        {
          "video_id": "abc-123",
          "procedure": "Laparoscopic Cholecystectomy",
          "local_path": "uploads/videos/abc-123_surgery.mp4",
          "status": "completed",
          "processed": true,
          "vlm_summary": "Full text...",
          "vlm_phases": [
            {
              "timestamp_range": "0:00-0:45",
              "description": "...",
              "key_timestamp": "0:23",
              "key_frame_data": "base64..."
            }
          ],
          "vlm_latency": 25.4
        }
```

## Troubleshooting

### VLM Processing Fails

**Check OpenRouter API Key:**
```bash
# Verify key is set
echo $OPENROUTER_API_KEY

# Or check .env file
cat .env | grep OPENROUTER
```

**Check Logs:**
```bash
# Backend console will show:
# "Starting background VLM processing for video: abc-123"
# "VLM processing completed for abc-123: 5 phases found"
```

**Check Metadata:**
```bash
cat uploads/metadata/{video_id}.json
```

If `status: "error"`, check `error_message` field.

### Missing Dependencies

```bash
pip install opencv-python openai
```

### Frame Extraction Fails

**Issue**: Video codec not supported

**Solution**: Convert video to standard MP4:
```bash
ffmpeg -i input.mov -c:v libx264 output.mp4
```

### API Rate Limits

OpenRouter free tier has rate limits. If you hit limits:
- Wait and retry
- Upgrade to paid tier
- Reduce `fps` parameter (extract fewer frames)

## Configuration Options

### Adjust Frame Extraction Rate

Edit `src/docuhelp/ui/api/routes/video.py`:

```python
# Change fps parameter (default: 1 frame/sec)
result = run_vlm_inference_pipeline(video_id, fps=0.5)  # 1 frame every 2 seconds
```

### Limit Maximum Frames

```python
# Process only first 60 frames
result = run_vlm_inference_pipeline(video_id, fps=1, max_frames=60)
```

### Custom VLM Prompt

Edit `src/docuhelp/vlm/openrouter_client.py`:

```python
def _build_default_prompt(self, procedure):
    return "Your custom prompt here..."
```

## Testing

### Test Frame Extraction

```python
from docuhelp.vlm.video_processor import extract_frames_from_video

frames = extract_frames_from_video("uploads/videos/test.mp4", fps=1)
print(f"Extracted {len(frames)} frames")
print(f"First frame timestamp: {frames[0]['timestamp']}s")
```

### Test VLM Client

```python
from docuhelp.vlm.openrouter_client import create_vlm_client

client = create_vlm_client()
# Use test frames...
result = client.analyze_video_frames(frames, procedure="Test")
print(result['summary'])
```

### Test Full Pipeline

```python
from docuhelp.vlm.inference import run_vlm_inference_pipeline

# Assumes video is already uploaded with video_id
result = run_vlm_inference_pipeline(video_id="test-123")
print(f"Phases: {len(result['phases'])}")
```

## Cost Estimation

**OpenRouter Gemini 2.0 Flash Free Tier:**
- Free with rate limits
- Good for development and testing

**Paid Tier:**
- ~$0.01-0.05 per video (depending on length)
- 60-second video = ~60 frames = ~$0.02

---

**Status**: ✅ VLM Pipeline Ready
**Model**: Google Gemini 2.0 Flash (via OpenRouter)
**Processing**: Automatic background task
**Output**: Timestamped phases with key frames
