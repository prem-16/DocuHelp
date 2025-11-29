"""YouTube video parser for extracting metadata, timestamps, and subtitles."""
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import re
from datetime import datetime, timedelta
import json
import logging

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
    TRANSCRIPT_AVAILABLE = True
except ImportError:
    TRANSCRIPT_AVAILABLE = False

try:
    from pytubefix import YouTube
    PYTUBE_AVAILABLE = True
except ImportError:
    PYTUBE_AVAILABLE = False

logger = logging.getLogger(__name__)


class YouTubeParser:
    """Parser for YouTube videos to extract metadata, timestamps, and subtitles."""

    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """
        Extract YouTube video ID from various URL formats.

        Supported formats:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://www.youtube.com/embed/VIDEO_ID
        - https://www.youtube.com/v/VIDEO_ID

        Args:
            url: YouTube URL

        Returns:
            Video ID or None if invalid
        """
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([a-zA-Z0-9_-]{11})',
            r'(?:youtube\.com\/watch\?.*&v=)([a-zA-Z0-9_-]{11})',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        # If URL is just the video ID
        if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
            return url

        return None

    @staticmethod
    def parse_timestamp(timestamp_str: str) -> int:
        """
        Parse timestamp string to seconds.

        Supported formats:
        - HH:MM:SS
        - MM:SS
        - SS

        Args:
            timestamp_str: Timestamp string

        Returns:
            Total seconds
        """
        parts = timestamp_str.strip().split(':')
        parts = [int(p) for p in parts]

        if len(parts) == 3:  # HH:MM:SS
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2:  # MM:SS
            return parts[0] * 60 + parts[1]
        elif len(parts) == 1:  # SS
            return parts[0]
        else:
            raise ValueError(f"Invalid timestamp format: {timestamp_str}")

    @staticmethod
    def format_timestamp(seconds: int) -> str:
        """
        Format seconds to HH:MM:SS or MM:SS.

        Args:
            seconds: Total seconds

        Returns:
            Formatted timestamp string
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

    def extract_url_timestamp(self, url: str) -> Optional[int]:
        """
        Extract timestamp parameter from YouTube URL (?t=XXs or &t=XXs).

        Args:
            url: YouTube URL

        Returns:
            Timestamp in seconds or None
        """
        # Match ?t=123 or &t=123 or ?t=123s or &t=123s
        match = re.search(r'[?&]t=(\d+)s?', url)
        if match:
            return int(match.group(1))
        return None

    def get_video_metadata(self, url: str, use_oauth: bool = False, allow_oauth_cache: bool = True) -> Dict:
        """
        Extract video metadata using pytubefix.

        Args:
            url: YouTube URL
            use_oauth: Use OAuth authentication for age-restricted videos
            allow_oauth_cache: Allow caching of OAuth credentials

        Returns:
            Dictionary with video metadata
        """
        if not PYTUBE_AVAILABLE:
            raise ImportError(
                "pytubefix is not installed. Install it with: pip install pytubefix"
            )

        video_id = self.extract_video_id(url)
        if not video_id:
            raise ValueError(f"Invalid YouTube URL: {url}")

        try:
            yt = YouTube(
                f"https://www.youtube.com/watch?v={video_id}",
                use_oauth=use_oauth,
                allow_oauth_cache=allow_oauth_cache
            )

            metadata = {
                'video_id': video_id,
                'title': yt.title,
                'author': yt.author,
                'length': yt.length,  # Duration in seconds
                'duration_formatted': self.format_timestamp(yt.length),
                'description': yt.description,
                'views': yt.views,
                'publish_date': yt.publish_date.isoformat() if yt.publish_date else None,
                'thumbnail_url': yt.thumbnail_url,
                'rating': yt.rating,
                'url': f"https://www.youtube.com/watch?v={video_id}",
                'url_timestamp': self.extract_url_timestamp(url),
            }

            logger.info(f"Extracted metadata for video: {video_id} - {yt.title}")
            return metadata

        except Exception as e:
            error_msg = str(e)

            # Check if it's an age restriction error and retry with OAuth
            if "age restricted" in error_msg.lower() and not use_oauth:
                logger.info(
                    f"\n{'='*60}\n"
                    f"Video {video_id} is age-restricted!\n"
                    f"{'='*60}\n"
                    f"Automatically switching to OAuth authentication...\n"
                    f"You will be prompted to authenticate with your Google account.\n"
                    f"{'='*60}"
                )
                try:
                    return self.get_video_metadata(url, use_oauth=True, allow_oauth_cache=allow_oauth_cache)
                except Exception as oauth_error:
                    logger.error(
                        f"\n{'='*60}\n"
                        f"Failed to access age-restricted video {video_id}\n"
                        f"{'='*60}\n"
                        f"Error: {oauth_error}\n"
                        f"Note: You need to complete the OAuth authentication to access this video.\n"
                        f"{'='*60}"
                    )
                    raise

            logger.error(f"Failed to extract metadata for {video_id}: {e}")
            raise

    def get_subtitles(
        self,
        video_id: str,
        languages: Optional[List[str]] = None
    ) -> Dict[str, List[Dict]]:
        """
        Extract subtitles/captions from YouTube video.

        Args:
            video_id: YouTube video ID
            languages: List of language codes to try (e.g., ['en', 'es'])
                      If None, tries English first, then any available

        Returns:
            Dictionary mapping language codes to subtitle data:
            {
                'en': [
                    {'text': 'Hello', 'start': 0.0, 'duration': 2.5},
                    ...
                ]
            }
        """
        if not TRANSCRIPT_AVAILABLE:
            raise ImportError(
                "youtube-transcript-api is not installed. "
                "Install it with: pip install youtube-transcript-api"
            )

        if languages is None:
            languages = ['en', 'en-US', 'en-GB']

        subtitles = {}

        try:
            # Get list of available transcripts
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # Try to get requested languages
            for lang in languages:
                try:
                    transcript = transcript_list.find_transcript([lang])
                    subtitle_data = transcript.fetch()
                    subtitles[lang] = subtitle_data
                    logger.info(f"Found {lang} subtitles for {video_id}")
                    break  # Stop after finding first match
                except NoTranscriptFound:
                    continue

            # If no requested language found, try auto-generated English
            if not subtitles:
                try:
                    transcript = transcript_list.find_generated_transcript(['en'])
                    subtitle_data = transcript.fetch()
                    subtitles['en-auto'] = subtitle_data
                    logger.info(f"Found auto-generated English subtitles for {video_id}")
                except NoTranscriptFound:
                    pass

            # If still nothing, get any available transcript
            if not subtitles:
                try:
                    available = list(transcript_list)
                    if available:
                        first_transcript = available[0]
                        subtitle_data = first_transcript.fetch()
                        subtitles[first_transcript.language_code] = subtitle_data
                        logger.info(
                            f"Found {first_transcript.language_code} subtitles for {video_id}"
                        )
                except Exception as e:
                    logger.warning(f"Could not fetch any subtitles: {e}")

        except TranscriptsDisabled:
            logger.warning(f"Subtitles are disabled for video {video_id}")
        except Exception as e:
            logger.error(f"Error fetching subtitles for {video_id}: {e}")

        return subtitles

    def parse_description_timestamps(self, description: str) -> List[Dict]:
        """
        Parse timestamps from video description.

        Common formats:
        - 0:00 Introduction
        - 1:23 - Main content
        - [2:45] Section name
        - 03:30 Another section

        Args:
            description: Video description text

        Returns:
            List of dictionaries with parsed timestamps:
            [
                {'time': 0, 'time_formatted': '0:00', 'label': 'Introduction'},
                ...
            ]
        """
        timestamps = []
        lines = description.split('\n')

        # Pattern to match timestamps
        timestamp_pattern = r'\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?\s*[-:]?\s*(.+)'

        for line in lines:
            line = line.strip()
            match = re.match(timestamp_pattern, line)

            if match:
                time_str = match.group(1)
                label = match.group(2).strip()

                try:
                    time_seconds = self.parse_timestamp(time_str)
                    timestamps.append({
                        'time': time_seconds,
                        'time_formatted': time_str,
                        'label': label
                    })
                except ValueError:
                    continue

        logger.info(f"Found {len(timestamps)} timestamps in description")
        return timestamps

    def parse_youtube_video(
        self,
        url: str,
        extract_subtitles: bool = True,
        subtitle_languages: Optional[List[str]] = None,
        use_oauth: bool = False,
        allow_oauth_cache: bool = True
    ) -> Dict:
        """
        Complete parsing of YouTube video.

        Args:
            url: YouTube URL
            extract_subtitles: Whether to extract subtitles
            subtitle_languages: List of language codes for subtitles
            use_oauth: Use OAuth authentication for age-restricted videos
            allow_oauth_cache: Allow caching of OAuth credentials

        Returns:
            Complete video data including metadata, timestamps, and subtitles
        """
        video_id = self.extract_video_id(url)
        if not video_id:
            raise ValueError(f"Invalid YouTube URL: {url}")

        # Get metadata
        metadata = self.get_video_metadata(url, use_oauth, allow_oauth_cache)

        # Parse timestamps from description
        description_timestamps = []
        if metadata.get('description'):
            description_timestamps = self.parse_description_timestamps(
                metadata['description']
            )

        # Get subtitles
        subtitles = {}
        if extract_subtitles:
            try:
                subtitles = self.get_subtitles(video_id, subtitle_languages)
            except Exception as e:
                logger.warning(f"Could not extract subtitles: {e}")

        result = {
            'video_id': video_id,
            'url': url,
            'metadata': metadata,
            'description_timestamps': description_timestamps,
            'subtitles': subtitles,
            'has_subtitles': len(subtitles) > 0,
            'subtitle_languages': list(subtitles.keys()),
            'parsed_at': datetime.now().isoformat(),
        }

        logger.info(
            f"Successfully parsed YouTube video {video_id}: "
            f"{len(description_timestamps)} timestamps, "
            f"{len(subtitles)} subtitle tracks"
        )

        return result

    def save_parsed_data(self, parsed_data: Dict, output_path: Path) -> None:
        """
        Save parsed video data to JSON file.

        Args:
            parsed_data: Parsed video data dictionary
            output_path: Path to save JSON file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved parsed data to {output_path}")


def parse_youtube_url(
    url: str,
    extract_subtitles: bool = True,
    subtitle_languages: Optional[List[str]] = None,
    use_oauth: bool = False,
    allow_oauth_cache: bool = True
) -> Dict:
    """
    Convenience function to parse YouTube video.

    Args:
        url: YouTube URL
        extract_subtitles: Whether to extract subtitles
        subtitle_languages: List of language codes for subtitles
        use_oauth: Use OAuth authentication for age-restricted videos
        allow_oauth_cache: Allow caching of OAuth credentials

    Returns:
        Parsed video data
    """
    parser = YouTubeParser()
    return parser.parse_youtube_video(url, extract_subtitles, subtitle_languages, use_oauth, allow_oauth_cache)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Example URL with timestamp
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s"

    parser = YouTubeParser()

    # Test video ID extraction
    video_id = parser.extract_video_id(test_url)
    print(f"Video ID: {video_id}")

    # Test URL timestamp extraction
    url_time = parser.extract_url_timestamp(test_url)
    print(f"URL timestamp: {url_time}s")

    # Test timestamp parsing
    print(f"Parse '1:23': {parser.parse_timestamp('1:23')}s")
    print(f"Parse '1:23:45': {parser.parse_timestamp('1:23:45')}s")

    # Full parsing (uncomment to test with real video)
    # parsed = parser.parse_youtube_video(test_url)
    # print(json.dumps(parsed, indent=2))
