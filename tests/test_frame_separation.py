"""Test frame extraction with minimum time separation."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from docuhelp.vlm.video_processor import extract_frames_from_video


def test_minimum_time_separation():
    """Test that frames are extracted at least 30 seconds apart."""

    # Find a test video
    video_dir = Path("frontend/uploads/videos")
    if not video_dir.exists():
        print("No video directory found. Skipping test.")
        return

    # Find first video file
    video_files = list(video_dir.glob("*.mp4"))
    if not video_files:
        print("No video files found. Skipping test.")
        return

    video_path = str(video_files[0])
    print(f"\nTesting frame extraction on: {video_path}")
    print("=" * 70)

    # Test with 30 second minimum separation
    min_separation = 30.0
    frames = extract_frames_from_video(
        video_path,
        fps=1,
        max_frames=10,
        min_time_separation=min_separation,
        filter_text=True,
        filter_duplicates=True
    )

    print(f"\nExtracted {len(frames)} frames")
    print("-" * 70)

    # Check timestamps
    timestamps = [f["timestamp"] for f in frames]
    print("\nFrame timestamps:")
    for i, ts in enumerate(timestamps):
        minutes = int(ts // 60)
        seconds = ts % 60
        print(f"  Frame {i+1}: {minutes}:{seconds:05.2f} ({ts:.2f}s)")

    # Verify minimum separation
    print(f"\nVerifying minimum {min_separation}s separation:")
    all_valid = True
    for i in range(1, len(timestamps)):
        gap = timestamps[i] - timestamps[i-1]
        status = "[OK]" if gap >= min_separation else "[FAIL]"
        print(f"  {status} Frame {i} to {i+1}: {gap:.2f}s")
        if gap < min_separation:
            all_valid = False

    if all_valid:
        print(f"\n[SUCCESS] All frames are at least {min_separation}s apart!")
    else:
        print(f"\n[FAILED] Some frames are closer than {min_separation}s")

    return all_valid


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    test_minimum_time_separation()
