"""Test script for YouTube video downloader."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import logging
from docuhelp.dataset.youtube_downloader import YouTubeDownloader, download_youtube_video

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

logger = logging.getLogger(__name__)


def test_single_video_download():
    """Test downloading a single YouTube video."""
    print("=" * 80)
    print("TEST 1: Single Video Download")
    print("=" * 80)

    # Example video URL (replace with your surgical procedure video)
    test_url = "https://youtu.be/uYRbY1uVHTc?si=hbcVoxtj4khLFWHD"
    downloader = YouTubeDownloader(download_dir=Path("downloads/youtube_test"))

    print(f"URL: {test_url}")
    print("Starting download...")
    print()

    try:
        result = downloader.download_video(
            url=test_url,
            quality='720p',  # Download in 720p quality
            download_subtitles=True,
            subtitle_languages=['en'],
            extract_metadata=True
        )

        print()
        print("SUCCESS!")
        print("-" * 80)
        print(f"Title: {result['title']}")
        print(f"Video ID: {result['video_id']}")
        print(f"Video Path: {result['video_path']}")
        print(f"Video Directory: {result['video_dir']}")
        print(f"Metadata Path: {result['metadata_path']}")
        print(f"Thumbnail: {result['thumbnail_path']}")
        print(f"Subtitles: {len(result['subtitle_paths'])} files")
        if result['subtitle_paths']:
            for sub in result['subtitle_paths']:
                print(f"  - {sub}")
        print()
        print("Download Info:")
        print(f"  Duration: {result['download_info']['duration']}s")
        print(f"  Views: {result['download_info']['view_count']:,}")
        print(f"  Uploader: {result['download_info']['uploader']}")
        print(f"  Resolution: {result['download_info']['resolution']}")
        print(f"  File Size: {result['download_info']['filesize']:,} bytes" if result['download_info']['filesize'] else "  File Size: N/A")
        print()

        return True

    except Exception as e:
        print()
        print("FAILED!")
        print("-" * 80)
        print(f"Error: {e}")
        logger.exception("Download failed")
        return False


def test_audio_only_download():
    """Test downloading audio only (MP3)."""
    print("=" * 80)
    print("TEST 2: Audio-Only Download (MP3)")
    print("=" * 80)

    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    downloader = YouTubeDownloader(download_dir=Path("downloads/youtube_audio"))

    print(f"URL: {test_url}")
    print("Downloading audio only...")
    print()

    try:
        result = downloader.download_video(
            url=test_url,
            audio_only=True,
            extract_metadata=True
        )

        print()
        print("SUCCESS!")
        print("-" * 80)
        print(f"Title: {result['title']}")
        print(f"Audio Path: {result['video_path']}")
        print(f"Format: MP3")
        print()

        return True

    except Exception as e:
        print()
        print("FAILED!")
        print("-" * 80)
        print(f"Error: {e}")
        return False


def test_convenience_function():
    """Test the convenience download function."""
    print("=" * 80)
    print("TEST 3: Convenience Function")
    print("=" * 80)

    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    print(f"URL: {test_url}")
    print("Using download_youtube_video() convenience function...")
    print()

    try:
        result = download_youtube_video(
            url=test_url,
            output_dir=Path("downloads/youtube_convenience"),
            quality='480p',
            download_subtitles=True
        )

        print()
        print("SUCCESS!")
        print("-" * 80)
        print(f"Title: {result['title']}")
        print(f"Video Path: {result['video_path']}")
        print()

        return True

    except Exception as e:
        print()
        print("FAILED!")
        print("-" * 80)
        print(f"Error: {e}")
        return False


def test_age_restricted_video():
    """Test downloading an age-restricted video."""
    print("=" * 80)
    print("TEST 4: Age-Restricted Video")
    print("=" * 80)

    # Use the age-restricted video from earlier
    test_url = "https://youtu.be/uYRbY1uVHTc?si=hbcVoxtj4khLFWHD"

    downloader = YouTubeDownloader(download_dir=Path("downloads/youtube_age_restricted"))

    print(f"URL: {test_url}")
    print("This video is age-restricted. OAuth authentication will be used if needed.")
    print()

    try:
        result = downloader.download_video(
            url=test_url,
            quality='720p',
            download_subtitles=True,
            extract_metadata=True,
            use_oauth=False  # Let it auto-detect and switch to OAuth if needed
        )

        print()
        print("SUCCESS!")
        print("-" * 80)
        print(f"Title: {result['title']}")
        print(f"Video Path: {result['video_path']}")
        print()

        return True

    except Exception as e:
        print()
        print("FAILED!")
        print("-" * 80)
        print(f"Error: {e}")
        logger.exception("Download failed")
        return False


def test_custom_filename():
    """Test downloading with a custom filename."""
    print("=" * 80)
    print("TEST 5: Custom Filename")
    print("=" * 80)

    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    custom_name = "my_custom_video_name"

    downloader = YouTubeDownloader(download_dir=Path("downloads/youtube_custom"))

    print(f"URL: {test_url}")
    print(f"Custom filename: {custom_name}")
    print()

    try:
        result = downloader.download_video(
            url=test_url,
            quality='best',
            custom_filename=custom_name,
            extract_metadata=True
        )

        print()
        print("SUCCESS!")
        print("-" * 80)
        print(f"Video Path: {result['video_path']}")
        print(f"Expected filename: {custom_name}.mp4")
        print()

        return True

    except Exception as e:
        print()
        print("FAILED!")
        print("-" * 80)
        print(f"Error: {e}")
        return False


def main():
    """Run all tests."""
    print()
    print("#" * 80)
    print("#" + " " * 78 + "#")
    print("#" + " " * 20 + "YOUTUBE DOWNLOADER TEST SUITE" + " " * 29 + "#")
    print("#" + " " * 78 + "#")
    print("#" * 80)
    print()

    tests = [
        ("Single Video Download", test_single_video_download),
        ("Audio-Only Download", test_audio_only_download),
        ("Convenience Function", test_convenience_function),
        ("Custom Filename", test_custom_filename),
        # Uncomment to test age-restricted video (requires OAuth)
        # ("Age-Restricted Video", test_age_restricted_video),
    ]

    results = []

    for test_name, test_func in tests:
        print()
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"Test crashed: {e}")
            results.append((test_name, False))
        print()

    # Print summary
    print()
    print("#" * 80)
    print("TEST SUMMARY")
    print("#" * 80)
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        symbol = "✓" if success else "✗"
        print(f"{symbol} {test_name}: {status}")

    passed = sum(1 for _, success in results if success)
    total = len(results)
    print()
    print(f"Passed: {passed}/{total}")
    print("#" * 80)

    return passed == total


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)
