# YouTube Video Parser Guide

## Overview

The YouTube parser module provides comprehensive functionality to parse YouTube videos, extracting:
- Video metadata (title, author, duration, etc.)
- Timestamps from video descriptions
- Subtitles/captions in multiple languages
- URL parameters (including start time)

## Installation

Install required dependencies:

```bash
pip install pytube youtube-transcript-api
# OR install entire project
pip install -e .
```

## Features

### 1. Video ID Extraction

Supports multiple URL formats:
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/embed/VIDEO_ID`
- `https://www.youtube.com/v/VIDEO_ID`

```python
from src.docuhelp.dataset.youtube_parser import YouTubeParser

parser = YouTubeParser()
video_id = parser.extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
print(video_id)  # Output: dQw4w9WgXcQ
```

### 2. Timestamp Parsing

Parse timestamps from various formats:
- `HH:MM:SS` - Hours:Minutes:Seconds
- `MM:SS` - Minutes:Seconds
- `SS` - Seconds

```python
parser = YouTubeParser()

# Parse different formats
seconds = parser.parse_timestamp("1:23")      # 83 seconds
seconds = parser.parse_timestamp("1:23:45")   # 5025 seconds
seconds = parser.parse_timestamp("42")        # 42 seconds

# Format seconds back to timestamp
formatted = parser.format_timestamp(83)       # "01:23"
formatted = parser.format_timestamp(5025)     # "01:23:45"
```

### 3. Extract URL Timestamps

Extract start time from YouTube URLs with `?t=` or `&t=` parameters:

```python
parser = YouTubeParser()
url = "https://www.youtube.com/watch?v=VIDEO_ID&t=42s"
start_time = parser.extract_url_timestamp(url)
print(start_time)  # Output: 42
```

### 4. Parse Description Timestamps

Automatically extract chapter/section timestamps from video descriptions:

```python
description = """
Surgical Procedure Overview

Timestamps:
0:00 Introduction
1:30 Patient preparation
5:45 - Incision and access
[10:20] Main procedure
15:00 - Closure
"""

parser = YouTubeParser()
timestamps = parser.parse_description_timestamps(description)

# Output:
# [
#   {'time': 0, 'time_formatted': '0:00', 'label': 'Introduction'},
#   {'time': 90, 'time_formatted': '1:30', 'label': 'Patient preparation'},
#   ...
# ]
```

### 5. Extract Subtitles

Get subtitles/captions in multiple languages:

```python
parser = YouTubeParser()
video_id = "dQw4w9WgXcQ"

# Get English subtitles
subtitles = parser.get_subtitles(video_id, languages=['en'])

# Try multiple languages in order of preference
subtitles = parser.get_subtitles(video_id, languages=['en', 'es', 'fr'])

# Subtitle format:
# {
#   'en': [
#     {'text': 'Hello', 'start': 0.0, 'duration': 2.5},
#     {'text': 'Welcome', 'start': 2.5, 'duration': 1.8},
#     ...
#   ]
# }
```

### 6. Complete Video Parsing

Parse all available data from a YouTube video:

```python
from src.docuhelp.dataset.youtube_parser import parse_youtube_url

# Full parsing with all features
result = parse_youtube_url(
    url="https://www.youtube.com/watch?v=VIDEO_ID",
    extract_subtitles=True,
    subtitle_languages=['en']
)

# Result structure:
# {
#   'video_id': 'VIDEO_ID',
#   'url': 'https://...',
#   'metadata': {
#     'title': '...',
#     'author': '...',
#     'length': 1234,  # seconds
#     'duration_formatted': '20:34',
#     'description': '...',
#     'views': 1000000,
#     'publish_date': '2024-01-01T00:00:00',
#     'thumbnail_url': 'https://...',
#   },
#   'description_timestamps': [...],
#   'subtitles': {...},
#   'has_subtitles': True,
#   'subtitle_languages': ['en'],
#   'parsed_at': '2024-01-01T12:00:00'
# }
```

## Unified Video Input Parser

Use the unified parser to handle both YouTube URLs and file uploads:

```python
from src.docuhelp.dataset.video_input_parser import parse_video_input

# Parse YouTube URL
youtube_data = parse_video_input(
    "https://www.youtube.com/watch?v=VIDEO_ID",
    metadata={'procedure_type': 'laparoscopy'}
)

# Parse uploaded file
with open('surgery_video.mp4', 'rb') as f:
    file_data = parse_video_input(
        f,
        filename='surgery_video.mp4',
        metadata={'procedure_type': 'laparoscopy'}
    )

# Parse local file path
local_data = parse_video_input(
    "/path/to/video.mp4",
    metadata={'procedure_type': 'laparoscopy'}
)
```

## Usage in API Endpoints

Example FastAPI endpoint:

```python
from fastapi import APIRouter, UploadFile, Form
from src.docuhelp.dataset.video_input_parser import parse_video_input

router = APIRouter()

@router.post("/parse-video")
async def parse_video(
    youtube_url: Optional[str] = Form(None),
    video_file: Optional[UploadFile] = Form(None),
    procedure_type: str = Form(...)
):
    metadata = {'procedure_type': procedure_type}

    if youtube_url:
        result = parse_video_input(
            youtube_url,
            metadata=metadata,
            extract_youtube_subtitles=True
        )
    elif video_file:
        result = parse_video_input(
            video_file.file,
            filename=video_file.filename,
            metadata=metadata
        )
    else:
        raise ValueError("Provide either youtube_url or video_file")

    return result
```

## Testing

Run the test script:

```bash
python test_youtube_parser.py
```

This will test:
- Video ID extraction
- Timestamp parsing
- URL timestamp extraction
- Description timestamp parsing
- Full video metadata extraction
- Subtitle extraction

## Key Classes and Functions

### YouTubeParser Class
- `extract_video_id(url)` - Extract video ID from URL
- `parse_timestamp(timestamp_str)` - Convert timestamp to seconds
- `format_timestamp(seconds)` - Convert seconds to HH:MM:SS
- `extract_url_timestamp(url)` - Get start time from URL
- `get_video_metadata(url)` - Get complete video metadata
- `get_subtitles(video_id, languages)` - Extract subtitles
- `parse_description_timestamps(description)` - Find timestamps in text
- `parse_youtube_video(url, extract_subtitles, subtitle_languages)` - Full parse

### VideoInputParser Class
- `detect_input_type(input_data)` - Detect if YouTube URL, file upload, or local file
- `parse_input(input_data, filename, metadata)` - Parse any video input type

### Convenience Functions
- `parse_youtube_url(url, extract_subtitles, subtitle_languages)` - Quick YouTube parse
- `parse_video_input(input_data, filename, metadata)` - Quick unified parse

## File Locations

- [src/docuhelp/dataset/youtube_parser.py](src/docuhelp/dataset/youtube_parser.py) - YouTube-specific parser
- [src/docuhelp/dataset/video_input_parser.py](src/docuhelp/dataset/video_input_parser.py) - Unified input parser
- [src/docuhelp/dataset/loader.py](src/docuhelp/dataset/loader.py) - File upload parser
- [test_youtube_parser.py](test_youtube_parser.py) - Test script

## Next Steps

1. Integrate with OpenRouter API for video analysis
2. Connect to Firebase for storage and data persistence
3. Create FastAPI endpoints for frontend integration
4. Add video frame extraction for visual analysis

## Notes

- YouTube API changes may affect pytube functionality
- Subtitles may not be available for all videos
- Some videos may have restricted access or age verification
- Consider rate limiting when parsing many videos
