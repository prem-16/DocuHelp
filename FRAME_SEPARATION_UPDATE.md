# Frame Extraction - Minimum Time Separation Update

## Summary
Updated the frame extraction system to ensure that extracted frames are at least **30 seconds apart** from each other, providing better diversity and coverage across the video timeline.

## Changes Made

### 1. Video Processor ([src/docuhelp/vlm/video_processor.py](src/docuhelp/vlm/video_processor.py))

Added `min_time_separation` parameter to `extract_frames_from_video()`:

```python
def extract_frames_from_video(
    video_path: str,
    fps: int = 1,
    max_frames: int = None,
    filter_text: bool = True,
    filter_duplicates: bool = True,
    min_time_separation: float = 30.0  # NEW PARAMETER
) -> List[Dict[str, any]]:
```

**Implementation Details:**
- When extracting frames, the system now tracks the timestamp of the last accepted frame
- Before accepting a new frame, it checks if at least `min_time_separation` seconds have passed
- Frames that are too close in time are filtered out and logged
- Works for both FPS-based extraction and max_frames-based extraction

**Key Features:**
1. **Smart Candidate Generation**: When using `max_frames`, generates 5x candidates to ensure enough frames pass all filters
2. **Pre-filtering**: Calculates candidate frame positions that respect the minimum time separation
3. **Real-time Validation**: Double-checks time separation before accepting each frame
4. **Detailed Logging**: Reports how many frames were filtered for each reason (text/title, duplicates, time separation)

### 2. VLM Inference Pipeline ([src/docuhelp/vlm/inference.py](src/docuhelp/vlm/inference.py))

Updated `run_vlm_inference_pipeline()` to expose the parameter:

```python
def run_vlm_inference_pipeline(
    video_id: str,
    fps: int = 1,
    max_frames: Optional[int] = None,
    min_time_separation: float = 30.0  # NEW PARAMETER
) -> Dict[str, any]:
```

The parameter is passed through to `extract_frames_from_video()`.

### 3. API Routes ([src/docuhelp/ui/api/routes/video.py](src/docuhelp/ui/api/routes/video.py))

Updated the background VLM processing task to use 30-second separation:

```python
# Run VLM inference (extracts frames and analyzes)
# Use 30 second minimum separation to ensure diverse frames
result = run_vlm_inference_pipeline(video_id, fps=1, min_time_separation=30.0)
```

## Test Results

Created [tests/test_frame_separation.py](tests/test_frame_separation.py) to verify the implementation.

**Test Video:** 10-minute surgical video (600 seconds)
**Requested Frames:** 10 frames maximum
**Actual Extracted:** 7 frames

**Frame Timestamps:**
| Frame | Time      | Seconds | Gap from Previous |
|-------|-----------|---------|-------------------|
| 1     | 0:00.00   | 0.00s   | -                 |
| 2     | 0:36.00   | 36.00s  | **36.00s** ✓      |
| 3     | 1:12.00   | 72.00s  | **36.00s** ✓      |
| 4     | 1:48.00   | 108.00s | **36.00s** ✓      |
| 5     | 3:00.00   | 180.00s | **72.00s** ✓      |
| 6     | 4:48.00   | 288.00s | **108.00s** ✓     |
| 7     | 9:36.00   | 576.00s | **288.00s** ✓     |

✅ **All frames are at least 30 seconds apart!**

## Benefits

1. **Better Video Coverage**: Frames are more evenly distributed across the video timeline
2. **Reduced Redundancy**: Eliminates frames from similar timepoints that might show the same surgical phase
3. **More Diverse Analysis**: VLM receives frames from different parts of the procedure
4. **Cost Effective**: Fewer but more meaningful frames sent to VLM API
5. **Configurable**: The `min_time_separation` parameter can be adjusted per use case

## Filtering Pipeline

The complete frame filtering pipeline now includes:

1. **Candidate Generation**: Generate frame positions based on fps or max_frames
2. **Time Separation Filter**: Ensure minimum time gap between frames
3. **Text Detection Filter**: Skip title/instruction screens with excessive text
4. **Surgical Content Filter**: Verify frame contains surgical content (color variance, proper brightness)
5. **Duplicate Detection Filter**: Remove visually similar frames using histogram comparison

## Usage Example

```python
from docuhelp.vlm.video_processor import extract_frames_from_video

# Extract up to 10 frames, at least 30 seconds apart
frames = extract_frames_from_video(
    video_path="video.mp4",
    max_frames=10,
    min_time_separation=30.0,  # 30 seconds minimum
    filter_text=True,
    filter_duplicates=True
)

# For longer videos, might want 60-second separation
frames = extract_frames_from_video(
    video_path="long_video.mp4",
    max_frames=20,
    min_time_separation=60.0,  # 1 minute minimum
    filter_text=True,
    filter_duplicates=True
)
```

## Files Modified

1. `src/docuhelp/vlm/video_processor.py` - Core frame extraction logic
2. `src/docuhelp/vlm/inference.py` - VLM pipeline interface
3. `src/docuhelp/ui/api/routes/video.py` - API endpoint configuration

## Files Created

1. `tests/test_frame_separation.py` - Test script to verify minimum separation
2. `FRAME_SEPARATION_UPDATE.md` - This documentation

## Default Configuration

- **Minimum Time Separation**: 30.0 seconds
- **Maximum Frames**: 20 frames (in API route)
- **FPS**: 1 frame per second (before filtering)

These defaults ensure good coverage for typical 5-15 minute surgical videos while keeping API costs reasonable.
