"""YouTube video downloader with metadata storage using yt-dlp."""
from typing import Dict, Optional, List, Callable
from pathlib import Path
import json
import logging
from datetime import datetime
import re

try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False

from docuhelp.dataset.youtube_parser import YouTubeParser

logger = logging.getLogger(__name__)


class YouTubeDownloader:
    """Download YouTube videos and store metadata."""

    def __init__(self, download_dir: Optional[Path] = None):
        """
        Initialize YouTube downloader.

        Args:
            download_dir: Directory to save downloaded videos. Defaults to ./downloads/youtube
        """
        if not YT_DLP_AVAILABLE:
            raise ImportError(
                "yt-dlp is not installed. Install it with: pip install yt-dlp"
            )

        self.download_dir = download_dir or Path("downloads/youtube")
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.parser = YouTubeParser()
        self._check_ffmpeg()

    def _check_ffmpeg(self) -> bool:
        """
        Check if FFmpeg is installed.

        Returns:
            True if FFmpeg is available, False otherwise
        """
        import subprocess
        try:
            subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                check=True,
                timeout=5
            )
            logger.info("FFmpeg is installed and available")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning(
                "\n" + "=" * 70 + "\n"
                "WARNING: FFmpeg not found!\n"
                "=" * 70 + "\n"
                "FFmpeg is REQUIRED for downloading and merging video/audio.\n"
                "Without it, downloads will fail or produce unplayable files.\n\n"
                "Install FFmpeg:\n"
                "  Windows (Chocolatey): choco install ffmpeg\n"
                "  Windows (Manual): https://www.gyan.dev/ffmpeg/builds/\n"
                "  Linux: sudo apt install ffmpeg\n"
                "  Mac: brew install ffmpeg\n"
                + "=" * 70
            )
            return False

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to be filesystem-safe.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Replace multiple spaces with single space
        filename = re.sub(r'\s+', ' ', filename)
        # Trim and limit length
        filename = filename.strip()[:200]
        return filename

    def _progress_hook(self, d: Dict) -> None:
        """
        Progress callback for yt-dlp.

        Args:
            d: Progress dictionary from yt-dlp
        """
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)

            if total > 0:
                percent = (downloaded / total) * 100
                speed = d.get('speed', 0)
                speed_str = f"{speed / 1024 / 1024:.2f} MB/s" if speed else "N/A"
                eta = d.get('eta', 0)

                logger.info(
                    f"Downloading: {percent:.1f}% | "
                    f"Speed: {speed_str} | "
                    f"ETA: {eta}s"
                )
        elif d['status'] == 'finished':
            logger.info(f"Download finished, now processing...")

    def download_video(
        self,
        url: str,
        quality: str = 'best',
        download_subtitles: bool = True,
        subtitle_languages: Optional[List[str]] = None,
        audio_only: bool = False,
        custom_filename: Optional[str] = None,
        extract_metadata: bool = True,
        use_oauth: bool = False,
        use_cookies_from_browser: Optional[str] = None,
        cookies_file: Optional[str] = None,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Download YouTube video with metadata.

        Args:
            url: YouTube URL
            quality: Video quality ('best', 'worst', '720p', '1080p', '480p', etc.)
            download_subtitles: Whether to download subtitles
            subtitle_languages: List of subtitle languages to download (e.g., ['en', 'es'])
            audio_only: Download only audio (MP3)
            custom_filename: Custom filename (without extension)
            extract_metadata: Extract and save metadata using YouTubeParser
            use_oauth: Use OAuth for age-restricted videos (pytubefix only)
            use_cookies_from_browser: Browser to extract cookies from ('chrome', 'firefox', 'edge', etc.)
            cookies_file: Path to Netscape cookies.txt file
            progress_callback: Custom progress callback function

        Returns:
            Dictionary with download information:
            {
                'video_id': str,
                'title': str,
                'video_path': str,
                'metadata_path': str,
                'subtitle_paths': List[str],
                'metadata': Dict,
                'download_info': Dict
            }
        """
        # Extract video ID
        video_id = self.parser.extract_video_id(url)
        if not video_id:
            raise ValueError(f"Invalid YouTube URL: {url}")

        logger.info(f"Starting download for video: {video_id}")

        # Extract metadata first (if enabled)
        metadata = {}
        if extract_metadata:
            try:
                logger.info("Extracting metadata with YouTubeParser...")
                parsed_data = self.parser.parse_youtube_video(
                    url,
                    extract_subtitles=False,  # We'll download them with yt-dlp
                    use_oauth=use_oauth
                )
                metadata = parsed_data
                logger.info(f"Metadata extracted: {metadata['metadata']['title']}")
            except Exception as e:
                logger.warning(f"Could not extract metadata with parser: {e}")
                logger.info("Continuing with yt-dlp download...")

        # Prepare download directory for this video
        video_dir = self.download_dir / video_id
        video_dir.mkdir(parents=True, exist_ok=True)

        # Set up filename
        if custom_filename:
            filename = self._sanitize_filename(custom_filename)
        elif metadata and 'metadata' in metadata:
            filename = self._sanitize_filename(metadata['metadata']['title'])
        else:
            filename = video_id

        # Configure yt-dlp options
        ydl_opts = {
            'outtmpl': str(video_dir / f"{filename}.%(ext)s"),
            'progress_hooks': [progress_callback or self._progress_hook],
            'writeinfojson': True,  # Save yt-dlp's own metadata
            'writethumbnail': True,  # Download thumbnail
            'writedescription': True,  # Save description
            'writesubtitles': download_subtitles,
            'writeautomaticsub': download_subtitles,
            'quiet': False,
            'no_warnings': False,
        }

        # Add cookie support for age-restricted videos
        if use_cookies_from_browser:
            ydl_opts['cookiesfrombrowser'] = (use_cookies_from_browser,)
            logger.info(f"Using cookies from browser: {use_cookies_from_browser}")
        elif cookies_file:
            ydl_opts['cookiefile'] = cookies_file
            logger.info(f"Using cookies from file: {cookies_file}")

        # Quality settings
        if audio_only:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            if quality == 'best':
                ydl_opts['format'] = 'bestvideo+bestaudio/best'
            elif quality == 'worst':
                ydl_opts['format'] = 'worstvideo+worstaudio/worst'
            else:
                # Specific quality (e.g., '720p')
                height = quality.replace('p', '')
                ydl_opts['format'] = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]'

            # Merge to mp4
            ydl_opts['merge_output_format'] = 'mp4'

        # Subtitle settings
        if download_subtitles:
            if subtitle_languages:
                ydl_opts['subtitleslangs'] = subtitle_languages
            else:
                ydl_opts['subtitleslangs'] = ['en']

        # OAuth settings for age-restricted videos
        if use_oauth:
            ydl_opts['username'] = 'oauth2'
            ydl_opts['password'] = ''

        # Download with yt-dlp
        download_info = {}
        video_path = None
        subtitle_paths = []

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"Downloading video from: {url}")
                download_info = ydl.extract_info(url, download=True)

                # Determine actual video path
                if audio_only:
                    video_path = video_dir / f"{filename}.mp3"
                else:
                    video_path = video_dir / f"{filename}.mp4"

                # Find subtitle files
                for file in video_dir.glob(f"{filename}*.vtt"):
                    subtitle_paths.append(str(file))
                for file in video_dir.glob(f"{filename}*.srt"):
                    subtitle_paths.append(str(file))

                logger.info(f"Download completed: {video_path}")

        except Exception as e:
            error_msg = str(e).lower()

            # Check if it's age-restricted
            if ("age" in error_msg and "restrict" in error_msg) or "sign in to confirm" in error_msg:
                # If we haven't tried cookies yet, try with browser cookies
                if not use_cookies_from_browser and not cookies_file:
                    logger.warning(
                        f"\n{'='*70}\n"
                        f"Video {video_id} is age-restricted!\n"
                        f"{'='*70}\n"
                        f"Attempting to use cookies from your browser...\n"
                    )
                    # Try Chrome first (most common)
                    try:
                        return self.download_video(
                            url=url,
                            quality=quality,
                            download_subtitles=download_subtitles,
                            subtitle_languages=subtitle_languages,
                            audio_only=audio_only,
                            custom_filename=custom_filename,
                            extract_metadata=extract_metadata,
                            use_oauth=use_oauth,
                            use_cookies_from_browser='chrome',
                            progress_callback=progress_callback
                        )
                    except Exception as chrome_error:
                        # If Chrome fails, provide helpful error message
                        logger.error(
                            f"\n{'='*70}\n"
                            f"Failed to download age-restricted video: {video_id}\n"
                            f"{'='*70}\n"
                            f"To download age-restricted videos, you need to:\n\n"
                            f"1. Be logged into YouTube in your browser (Chrome/Firefox/Edge)\n"
                            f"2. Use one of these options:\n\n"
                            f"   Option A - Use browser cookies (automatic):\n"
                            f"   downloader.download_video(\n"
                            f"       url='{url}',\n"
                            f"       use_cookies_from_browser='chrome'  # or 'firefox', 'edge'\n"
                            f"   )\n\n"
                            f"   Option B - Export cookies manually:\n"
                            f"   See: https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp\n"
                            f"{'='*70}\n"
                            f"Original error: {e}\n"
                            f"Chrome cookie error: {chrome_error}\n"
                            f"{'='*70}"
                        )
                        raise RuntimeError(
                            f"Age-restricted video requires authentication. "
                            f"Please ensure you're logged into YouTube in your browser and try again."
                        ) from e
                else:
                    # Already tried with cookies
                    logger.error(
                        f"\n{'='*70}\n"
                        f"Failed to download age-restricted video even with cookies\n"
                        f"{'='*70}\n"
                        f"Please ensure:\n"
                        f"1. You're logged into YouTube in your browser\n"
                        f"2. Your account can access this video\n"
                        f"3. Your browser is fully closed and reopened\n"
                        f"{'='*70}\n"
                        f"Error: {e}\n"
                        f"{'='*70}"
                    )
                    raise
            raise

        # Save our extracted metadata
        metadata_path = None
        if metadata:
            metadata_path = video_dir / f"{filename}_metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            logger.info(f"Metadata saved to: {metadata_path}")

        # Create comprehensive result
        result = {
            'video_id': video_id,
            'title': download_info.get('title', filename),
            'video_path': str(video_path),
            'video_dir': str(video_dir),
            'metadata_path': str(metadata_path) if metadata_path else None,
            'subtitle_paths': subtitle_paths,
            'thumbnail_path': str(video_dir / f"{filename}.jpg") if (video_dir / f"{filename}.jpg").exists() else None,
            'description_path': str(video_dir / f"{filename}.description") if (video_dir / f"{filename}.description").exists() else None,
            'info_json_path': str(video_dir / f"{filename}.info.json") if (video_dir / f"{filename}.info.json").exists() else None,
            'metadata': metadata,
            'download_info': {
                'duration': download_info.get('duration'),
                'upload_date': download_info.get('upload_date'),
                'uploader': download_info.get('uploader'),
                'view_count': download_info.get('view_count'),
                'like_count': download_info.get('like_count'),
                'channel': download_info.get('channel'),
                'resolution': download_info.get('resolution'),
                'fps': download_info.get('fps'),
                'filesize': download_info.get('filesize') or download_info.get('filesize_approx'),
            },
            'downloaded_at': datetime.now().isoformat(),
        }

        # Save combined result
        result_path = video_dir / f"{filename}_download_result.json"
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Download result saved to: {result_path}")
        logger.info(f"All files saved to: {video_dir}")

        return result

    def download_playlist(
        self,
        playlist_url: str,
        quality: str = 'best',
        download_subtitles: bool = True,
        max_downloads: Optional[int] = None,
        **kwargs
    ) -> List[Dict]:
        """
        Download entire YouTube playlist.

        Args:
            playlist_url: YouTube playlist URL
            quality: Video quality
            download_subtitles: Whether to download subtitles
            max_downloads: Maximum number of videos to download
            **kwargs: Additional arguments passed to download_video

        Returns:
            List of download results for each video
        """
        if not YT_DLP_AVAILABLE:
            raise ImportError("yt-dlp is required for playlist downloads")

        logger.info(f"Fetching playlist information: {playlist_url}")

        # Extract playlist info
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(playlist_url, download=False)

        if 'entries' not in playlist_info:
            raise ValueError("Not a valid playlist URL")

        videos = playlist_info['entries']
        if max_downloads:
            videos = videos[:max_downloads]

        logger.info(f"Found {len(videos)} videos in playlist")

        results = []
        for idx, video in enumerate(videos, 1):
            video_url = f"https://www.youtube.com/watch?v={video['id']}"
            logger.info(f"Downloading video {idx}/{len(videos)}: {video.get('title', video['id'])}")

            try:
                result = self.download_video(
                    url=video_url,
                    quality=quality,
                    download_subtitles=download_subtitles,
                    **kwargs
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to download {video_url}: {e}")
                results.append({
                    'video_id': video['id'],
                    'error': str(e),
                    'status': 'failed'
                })

        logger.info(f"Playlist download completed: {len([r for r in results if 'error' not in r])}/{len(videos)} successful")
        return results


def download_youtube_video(
    url: str,
    output_dir: Optional[Path] = None,
    quality: str = 'best',
    download_subtitles: bool = True,
    audio_only: bool = False,
    **kwargs
) -> Dict:
    """
    Convenience function to download a YouTube video.

    Args:
        url: YouTube URL
        output_dir: Directory to save video
        quality: Video quality ('best', '720p', '1080p', etc.)
        download_subtitles: Whether to download subtitles
        audio_only: Download only audio
        **kwargs: Additional arguments passed to YouTubeDownloader.download_video

    Returns:
        Download result dictionary
    """
    downloader = YouTubeDownloader(download_dir=output_dir)
    return downloader.download_video(
        url=url,
        quality=quality,
        download_subtitles=download_subtitles,
        audio_only=audio_only,
        **kwargs
    )


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s:%(name)s:%(message)s'
    )

    # Test with a video
    test_url = "https://www.youtube.com/watch?v=Xxu6VHSWmFI"

    print("=" * 80)
    print("YouTube Video Downloader Test")
    print("=" * 80)
    print(f"URL: {test_url}")
    print()

    downloader = YouTubeDownloader(download_dir=Path("downloads/youtube_test"))

    try:
        # Download video with best quality
        result = downloader.download_video(
            url=test_url,
            quality='480p',
            use_cookies_from_browser='firefox',
            download_subtitles=True,
            subtitle_languages=['en'],
            extract_metadata=True
        )

        print()
        print("Download Successful!")
        print("-" * 80)
        print(f"Title: {result['title']}")
        print(f"Video ID: {result['video_id']}")
        print(f"Video Path: {result['video_path']}")
        print(f"Metadata Path: {result['metadata_path']}")
        print(f"Subtitles: {len(result['subtitle_paths'])} files")
        print(f"Duration: {result['download_info']['duration']}s")
        print(f"Views: {result['download_info']['view_count']:,}")
        print(f"Directory: {result['video_dir']}")
        print()

    except Exception as e:
        print(f"Error: {e}")
        logger.exception("Download failed")
