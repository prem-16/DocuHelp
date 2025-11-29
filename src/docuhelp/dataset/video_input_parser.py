"""Unified video input parser supporting both file uploads and YouTube URLs."""
from typing import Dict, Optional, BinaryIO, Union
from pathlib import Path
from enum import Enum
import logging

from docuhelp.dataset.loader import parse_video_from_upload, validate_video_file
from docuhelp.dataset.youtube_parser import YouTubeParser, parse_youtube_url

logger = logging.getLogger(__name__)


class VideoInputType(Enum):
    """Types of video input sources."""
    FILE_UPLOAD = "file_upload"
    YOUTUBE_URL = "youtube_url"
    LOCAL_FILE = "local_file"


class VideoInputParser:
    """Unified parser for all types of video inputs."""

    def __init__(self):
        self.youtube_parser = YouTubeParser()

    def detect_input_type(self, input_data: Union[str, BinaryIO]) -> VideoInputType:
        """
        Detect the type of video input.

        Args:
            input_data: Can be a YouTube URL string, file path string, or file object

        Returns:
            VideoInputType enum
        """
        if isinstance(input_data, str):
            # Check if it's a YouTube URL
            video_id = self.youtube_parser.extract_video_id(input_data)
            if video_id:
                return VideoInputType.YOUTUBE_URL

            # Check if it's a local file path
            file_path = Path(input_data)
            if file_path.exists() and file_path.is_file():
                return VideoInputType.LOCAL_FILE

            raise ValueError(f"Invalid input: {input_data}")

        else:
            # Binary file object
            return VideoInputType.FILE_UPLOAD

    def parse_input(
        self,
        input_data: Union[str, BinaryIO],
        filename: Optional[str] = None,
        metadata: Optional[Dict] = None,
        extract_youtube_subtitles: bool = True,
        use_oauth: bool = False,
        allow_oauth_cache: bool = True
    ) -> Dict:
        """
        Parse any type of video input and return unified data structure.

        Args:
            input_data: YouTube URL, file path, or file object
            filename: Original filename (required for file uploads)
            metadata: Additional metadata
            extract_youtube_subtitles: Whether to extract subtitles from YouTube
            use_oauth: Use OAuth authentication for age-restricted YouTube videos
            allow_oauth_cache: Allow caching of OAuth credentials

        Returns:
            Unified video data dictionary:
            {
                'input_type': 'file_upload' | 'youtube_url' | 'local_file',
                'video_data': {...},  # Type-specific data
                'metadata': {...},
                'parsed_at': '...'
            }
        """
        input_type = self.detect_input_type(input_data)

        if input_type == VideoInputType.YOUTUBE_URL:
            return self._parse_youtube_input(
                input_data,
                metadata,
                extract_youtube_subtitles,
                use_oauth,
                allow_oauth_cache
            )

        elif input_type == VideoInputType.FILE_UPLOAD:
            if not filename:
                raise ValueError("Filename is required for file uploads")
            return self._parse_file_upload(input_data, filename, metadata)

        elif input_type == VideoInputType.LOCAL_FILE:
            return self._parse_local_file(input_data, metadata)

        else:
            raise ValueError(f"Unsupported input type: {input_type}")

    def _parse_youtube_input(
        self,
        url: str,
        metadata: Optional[Dict],
        extract_subtitles: bool,
        use_oauth: bool = False,
        allow_oauth_cache: bool = True
    ) -> Dict:
        """Parse YouTube URL input."""
        logger.info(f"Parsing YouTube URL: {url}")

        youtube_data = parse_youtube_url(
            url,
            extract_subtitles=extract_subtitles,
            use_oauth=use_oauth,
            allow_oauth_cache=allow_oauth_cache
        )

        return {
            'input_type': VideoInputType.YOUTUBE_URL.value,
            'video_data': youtube_data,
            'metadata': metadata or {},
            'source': 'youtube',
            'video_id': youtube_data['video_id'],
            'title': youtube_data['metadata']['title'],
            'duration': youtube_data['metadata']['length'],
            'has_subtitles': youtube_data['has_subtitles'],
            'timestamps': youtube_data['description_timestamps'],
        }

    def _parse_file_upload(
        self,
        file_content: BinaryIO,
        filename: str,
        metadata: Optional[Dict]
    ) -> Dict:
        """Parse uploaded file."""
        logger.info(f"Parsing file upload: {filename}")

        file_data = parse_video_from_upload(file_content, filename, metadata)

        return {
            'input_type': VideoInputType.FILE_UPLOAD.value,
            'video_data': file_data,
            'metadata': metadata or {},
            'source': 'upload',
            'filename': file_data['filename'],
            'file_path': file_data['temp_path'],
            'file_size': file_data['file_size'],
            'mime_type': file_data['mime_type'],
        }

    def _parse_local_file(
        self,
        file_path: str,
        metadata: Optional[Dict]
    ) -> Dict:
        """Parse local file path."""
        logger.info(f"Parsing local file: {file_path}")

        path = Path(file_path)
        if not validate_video_file(path):
            raise ValueError(f"Invalid video file: {file_path}")

        return {
            'input_type': VideoInputType.LOCAL_FILE.value,
            'video_data': {
                'file_path': str(path),
                'filename': path.name,
                'file_size': path.stat().st_size,
                'extension': path.suffix,
            },
            'metadata': metadata or {},
            'source': 'local',
            'filename': path.name,
            'file_path': str(path),
            'file_size': path.stat().st_size,
        }


def parse_video_input(
    input_data: Union[str, BinaryIO],
    filename: Optional[str] = None,
    metadata: Optional[Dict] = None,
    extract_youtube_subtitles: bool = True,
    use_oauth: bool = False,
    allow_oauth_cache: bool = True
) -> Dict:
    """
    Convenience function to parse any video input.

    Args:
        input_data: YouTube URL, file path, or file object
        filename: Original filename (required for file uploads)
        metadata: Additional metadata
        extract_youtube_subtitles: Whether to extract YouTube subtitles
        use_oauth: Use OAuth authentication for age-restricted YouTube videos
        allow_oauth_cache: Allow caching of OAuth credentials

    Returns:
        Parsed video data dictionary
    """
    parser = VideoInputParser()
    return parser.parse_input(
        input_data,
        filename,
        metadata,
        extract_youtube_subtitles,
        use_oauth,
        allow_oauth_cache
    )


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    parser = VideoInputParser()

    # Test YouTube URL
    print("=" * 60)
    print("Testing YouTube URL parsing...")
    print("=" * 60)

    youtube_url = "https://youtu.be/uYRbY1uVHTc?si=hbcVoxtj4khLFWHD"
    try:
        result = parser.parse_input(
            youtube_url,
            metadata={'procedure_type': 'test'}
        )
        print(f"Input type: {result['input_type']}")
        print(f"Video ID: {result.get('video_id')}")
        print(f"Title: {result.get('title')}")
        print(f"Duration: {result.get('duration')}s")
        print(f"Has subtitles: {result.get('has_subtitles')}")
        print(f"Timestamps found: {len(result.get('timestamps', []))}")
    except Exception as e:
        print(f"Error: {e}")
