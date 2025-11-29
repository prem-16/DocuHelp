# YouTube Video Downloader Guide

A comprehensive YouTube video downloader using `yt-dlp` with automatic metadata extraction and storage.

## Features

- ✅ Download YouTube videos in any quality (best, 720p, 1080p, 480p, etc.)
- ✅ Download audio-only (MP3 format)
- ✅ Automatic metadata extraction using YouTubeParser
- ✅ Download subtitles in multiple languages
- ✅ Download thumbnails and descriptions
- ✅ Handle age-restricted videos with OAuth
- ✅ Download entire playlists
- ✅ Progress tracking
- ✅ Organized file storage
- ✅ Custom filenames

## Installation

### Required Dependencies

```bash
# Install yt-dlp
pip install yt-dlp

# Install ffmpeg (REQUIRED for video downloads)
# Without FFmpeg, you can only use yt-dlp for metadata, not actual downloads

# Windows (using Chocolatey):
choco install ffmpeg

# Windows (manual):
# 1. Download from: https://ffmpeg.org/download.html
# 2. Extract to C:\ffmpeg
# 3. Add C:\ffmpeg\bin to your PATH

# Linux:
sudo apt install ffmpeg  # Ubuntu/Debian

# Mac:
brew install ffmpeg
```

### Optional Dependencies (for metadata extraction)

```bash
pip install pytubefix youtube-transcript-api
```

### Verify Installation

```bash
# Check yt-dlp
yt-dlp --version

# Check FFmpeg
ffmpeg -version
```

## Quick Start

### 1. Basic Video Download

```python
from pathlib import Path
from docuhelp.dataset.youtube_downloader import download_youtube_video

# Download a video
result = download_youtube_video(
    url="https://www.youtube.com/watch?v=VIDEO_ID",
    output_dir=Path("downloads"),
    quality='best',
    download_subtitles=True
)

print(f"Downloaded: {result['video_path']}")
print(f"Metadata: {result['metadata_path']}")
```

### 2. Using the YouTubeDownloader Class

```python
from pathlib import Path
from docuhelp.dataset.youtube_downloader import YouTubeDownloader

# Create downloader instance
downloader = YouTubeDownloader(download_dir=Path("downloads/youtube"))

# Download video
result = downloader.download_video(
    url="https://www.youtube.com/watch?v=VIDEO_ID",
    quality='720p',
    download_subtitles=True,
    subtitle_languages=['en', 'es'],
    extract_metadata=True
)
```

## Usage Examples

### Download Video in Specific Quality

```python
# 720p quality
result = downloader.download_video(
    url="https://www.youtube.com/watch?v=VIDEO_ID",
    quality='720p'
)

# Best available quality
result = downloader.download_video(
    url="https://www.youtube.com/watch?v=VIDEO_ID",
    quality='best'
)

# Worst quality (smallest file)
result = downloader.download_video(
    url="https://www.youtube.com/watch?v=VIDEO_ID",
    quality='worst'
)
```

### Download Audio Only (MP3)

```python
result = downloader.download_video(
    url="https://www.youtube.com/watch?v=VIDEO_ID",
    audio_only=True
)
# Downloads as MP3 file
```

### Download with Subtitles

```python
# Download English subtitles
result = downloader.download_video(
    url="https://www.youtube.com/watch?v=VIDEO_ID",
    download_subtitles=True,
    subtitle_languages=['en']
)

# Download multiple language subtitles
result = downloader.download_video(
    url="https://www.youtube.com/watch?v=VIDEO_ID",
    download_subtitles=True,
    subtitle_languages=['en', 'es', 'fr']
)
```

### Custom Filename

```python
result = downloader.download_video(
    url="https://www.youtube.com/watch?v=VIDEO_ID",
    custom_filename="my_surgical_procedure"
)
# Saves as: my_surgical_procedure.mp4
```

### Age-Restricted Videos

Age-restricted videos require authentication. The downloader will automatically detect and handle them, but for best results, use exported cookies:

```python
# Method 1: Use exported cookies (RECOMMENDED)
# Export cookies using browser extension first (see AGE_RESTRICTED_VIDEOS_GUIDE.md)
result = downloader.download_video(
    url="https://www.youtube.com/watch?v=AGE_RESTRICTED_VIDEO",
    cookies_file="youtube_cookies.txt",
    extract_metadata=False  # Skip pytubefix for age-restricted videos
)

# Method 2: Use browser cookies directly (may fail on Windows with Chrome)
result = downloader.download_video(
    url="https://www.youtube.com/watch?v=AGE_RESTRICTED_VIDEO",
    use_cookies_from_browser='firefox',  # firefox works better on Windows
    extract_metadata=False
)

# Method 3: Automatic (tries Chrome cookies automatically)
# Just call normally - it auto-detects and retries with cookies
result = downloader.download_video(
    url="https://www.youtube.com/watch?v=AGE_RESTRICTED_VIDEO"
)
```

**For detailed instructions, see [AGE_RESTRICTED_VIDEOS_GUIDE.md](AGE_RESTRICTED_VIDEOS_GUIDE.md)**

**Quick Script:**
```bash
python download_age_restricted.py
```

### Download Entire Playlist

```python
results = downloader.download_playlist(
    playlist_url="https://www.youtube.com/playlist?list=PLAYLIST_ID",
    quality='720p',
    download_subtitles=True,
    max_downloads=10  # Limit to first 10 videos
)

# Check results
for result in results:
    if 'error' not in result:
        print(f"Downloaded: {result['title']}")
    else:
        print(f"Failed: {result['error']}")
```

### Custom Progress Callback

```python
def my_progress_hook(d):
    if d['status'] == 'downloading':
        print(f"Progress: {d.get('_percent_str', 'N/A')}")
    elif d['status'] == 'finished':
        print("Download complete!")

result = downloader.download_video(
    url="https://www.youtube.com/watch?v=VIDEO_ID",
    progress_callback=my_progress_hook
)
```

## Output Structure

When you download a video, all files are organized in a folder structure:

```
downloads/youtube/
└── VIDEO_ID/
    ├── video_title.mp4                    # The video file
    ├── video_title.en.vtt                 # English subtitles
    ├── video_title.jpg                    # Thumbnail
    ├── video_title.description            # Video description
    ├── video_title.info.json              # yt-dlp metadata
    ├── video_title_metadata.json          # YouTubeParser metadata
    └── video_title_download_result.json   # Complete download info
```

## Returned Data Structure

```python
{
    'video_id': 'VIDEO_ID',
    'title': 'Video Title',
    'video_path': '/path/to/video.mp4',
    'video_dir': '/path/to/VIDEO_ID/',
    'metadata_path': '/path/to/metadata.json',
    'subtitle_paths': ['/path/to/subtitle.vtt'],
    'thumbnail_path': '/path/to/thumbnail.jpg',
    'description_path': '/path/to/description.txt',
    'info_json_path': '/path/to/info.json',
    'metadata': {
        # Full YouTubeParser metadata
        'video_id': 'VIDEO_ID',
        'metadata': {
            'title': 'Video Title',
            'author': 'Channel Name',
            'length': 300,  # seconds
            'duration_formatted': '05:00',
            'description': 'Full description...',
            'views': 1000000,
            'publish_date': '2024-01-01T00:00:00',
            # ... more metadata
        },
        'description_timestamps': [...],
        'subtitles': {...},
    },
    'download_info': {
        'duration': 300,
        'upload_date': '20240101',
        'uploader': 'Channel Name',
        'view_count': 1000000,
        'like_count': 50000,
        'channel': 'Channel Name',
        'resolution': '1280x720',
        'fps': 30,
        'filesize': 52428800,
    },
    'downloaded_at': '2024-01-15T10:30:00',
}
```

## Running Tests

```bash
# Install yt-dlp first
pip install yt-dlp

# Run the test suite
python test_youtube_downloader.py
```

The test suite includes:
- Single video download
- Audio-only download
- Convenience function test
- Custom filename test
- Age-restricted video test (optional)

## Metadata Extraction

The downloader integrates with `YouTubeParser` to extract comprehensive metadata:

- Video information (title, author, duration, views, etc.)
- Description timestamps for surgical procedures
- Subtitles/captions in multiple languages
- Thumbnail and video details

All metadata is saved to JSON files for easy processing and integration with your application.

## Error Handling

The downloader includes automatic error handling:

```python
try:
    result = downloader.download_video(url)
    print(f"Success: {result['video_path']}")
except ImportError as e:
    print(f"Missing dependency: {e}")
except ValueError as e:
    print(f"Invalid URL: {e}")
except Exception as e:
    print(f"Download failed: {e}")
```

## Tips & Best Practices

1. **Quality Selection**: Use `'720p'` for a good balance between quality and file size
2. **Subtitles**: Always enable subtitles for surgical videos for better accessibility
3. **Metadata**: Enable metadata extraction to get rich video information
4. **OAuth**: Keep OAuth enabled for institutional/medical videos that may be age-restricted
5. **File Organization**: Videos are automatically organized by video ID
6. **Playlists**: Use `max_downloads` to limit playlist downloads during testing

## Integration with DocuHelp

The downloader seamlessly integrates with the DocuHelp dataset pipeline:

```python
from docuhelp.dataset.youtube_downloader import download_youtube_video
from docuhelp.dataset.video_input_parser import parse_video_input

# Download video
result = download_youtube_video(
    url="https://www.youtube.com/watch?v=SURGICAL_VIDEO",
    quality='720p',
    download_subtitles=True
)

# Use downloaded video with video_input_parser
video_data = parse_video_input(
    input_data=result['video_path'],  # Use local file path
    metadata={
        'procedure_type': 'laparoscopic_surgery',
        'youtube_metadata': result['metadata']
    }
)
```

## Troubleshooting

### FFmpeg not found
Install ffmpeg: https://ffmpeg.org/download.html

### Age-restricted video fails
Use `use_oauth=True` parameter and complete the Google authentication

### Slow downloads
- Try lower quality: `quality='480p'`
- Check your internet connection
- Use audio-only if you only need the audio

### Subtitles not downloading
Some videos don't have subtitles. Check the result:
```python
if result['subtitle_paths']:
    print("Subtitles downloaded")
else:
    print("No subtitles available")
```

## API Reference

See [youtube_downloader.py](src/docuhelp/dataset/youtube_downloader.py) for complete API documentation.

## License

Part of the DocuHelp project.
