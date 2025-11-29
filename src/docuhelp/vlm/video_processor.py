"""
Video processing module to extract frames from MP4 files.
Converts video to images (1 frame per second) for VLM inference.
"""
import cv2
import base64
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import tempfile
import os
import numpy as np

logger = logging.getLogger(__name__)


def is_duplicate_frame(frame: np.ndarray, previous_frames: List[np.ndarray], threshold: float = 0.85) -> bool:
    """
    Check if a frame is too similar to previously extracted frames.
    Uses a stricter threshold (0.85) to ensure better frame separation.

    Args:
        frame: Current frame to check
        previous_frames: List of previously accepted frames
        threshold: Similarity threshold (0-1, higher means more similar required)

    Returns:
        True if frame is a duplicate
    """
    if not previous_frames:
        return False

    # Compare with ALL previous frames to ensure good separation
    frames_to_check = previous_frames

    for prev_frame in frames_to_check:
        # Calculate structural similarity using histogram comparison
        hist_current = cv2.calcHist([frame], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        hist_prev = cv2.calcHist([prev_frame], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])

        cv2.normalize(hist_current, hist_current)
        cv2.normalize(hist_prev, hist_prev)

        similarity = cv2.compareHist(hist_current, hist_prev, cv2.HISTCMP_CORREL)

        if similarity > threshold:
            return True

    return False


def has_too_much_text(frame: np.ndarray, text_ratio_threshold: float = 0.15) -> bool:
    """
    Detect if frame has too much text (likely a title/instruction screen).

    Args:
        frame: Frame to analyze
        text_ratio_threshold: Ratio of text pixels to total pixels (0-1)

    Returns:
        True if frame appears to be mostly text
    """
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Apply binary threshold to detect high contrast regions (text)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Edge detection to find text-like regions
        edges = cv2.Canny(gray, 100, 200)

        # Calculate ratio of edge pixels
        edge_ratio = np.count_nonzero(edges) / edges.size

        # Check for uniform background (common in title screens)
        std_dev = np.std(gray)

        # Title screens usually have:
        # 1. High edge ratio (text creates many edges)
        # 2. Low standard deviation (uniform background)
        # 3. Bimodal histogram (text vs background)

        if edge_ratio > text_ratio_threshold and std_dev < 40:
            logger.debug(f"Frame detected as text/title (edge_ratio={edge_ratio:.3f}, std={std_dev:.1f})")
            return True

        return False

    except Exception as e:
        logger.warning(f"Error in text detection: {e}")
        return False


def is_likely_surgical_content(frame: np.ndarray) -> bool:
    """
    Check if frame contains surgical content (not title/blank screen).

    Args:
        frame: Frame to analyze

    Returns:
        True if frame appears to contain surgical content
    """
    try:
        # Convert to HSV for better color analysis
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Surgical videos typically have:
        # 1. Varied colors (red/pink tissue, instruments, etc.)
        # 2. Good texture variance
        # 3. Not predominantly black/white

        # Check color variance
        h_std = np.std(hsv[:, :, 0])
        s_std = np.std(hsv[:, :, 1])

        # Check brightness - title screens are often very bright or very dark
        v_mean = np.mean(hsv[:, :, 2])

        # Surgical content has moderate variance and brightness
        has_color_variance = s_std > 20
        has_moderate_brightness = 30 < v_mean < 240

        return has_color_variance and has_moderate_brightness

    except Exception as e:
        logger.warning(f"Error in surgical content detection: {e}")
        return True  # Default to accepting frame


def extract_frames_from_video(
    video_path: str,
    fps: int = 1,
    max_frames: int = None,
    filter_text: bool = True,
    filter_duplicates: bool = True,
    min_time_separation: float = 30.0
) -> List[Dict[str, any]]:
    """
    Extract frames from video at specified FPS or equally distributed.
    Automatically filters out title/text screens and duplicate frames.

    Args:
        video_path: Path to MP4 video file
        fps: Frames per second to extract (default: 1 frame/sec, ignored if max_frames is set)
        max_frames: Maximum number of frames to extract equally distributed across video duration (None to use fps)
        filter_text: Filter out frames with too much text (title screens)
        filter_duplicates: Filter out duplicate/similar frames
        min_time_separation: Minimum time separation between frames in seconds (default: 30.0)

    Returns:
        List of dictionaries containing frame data:
        [
            {
                "timestamp": 1.0,  # seconds
                "frame_number": 30,
                "base64_image": "base64_encoded_string",
                "width": 1920,
                "height": 1080
            },
            ...
        ]
    """
    try:
        logger.info(f"Processing video: {video_path}")

        if not Path(video_path).exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Open video
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(f"Failed to open video: {video_path}")

        # Get video properties
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / video_fps
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        logger.info(f"Video properties: {width}x{height}, {video_fps} FPS, {duration:.2f}s duration")

        frames_data = []
        previous_frames = []  # For duplicate detection
        filtered_count = {"text": 0, "duplicate": 0, "time_separation": 0}
        last_accepted_timestamp = -min_time_separation  # Initialize to allow first frame

        # If max_frames is specified, extract frames equally distributed across the video
        if max_frames:
            logger.info(f"Extracting up to {max_frames} frames equally distributed across video (min {min_time_separation}s apart)")

            # Calculate which frames to extract for equal distribution
            # Extract more candidates to ensure we get max_frames after filtering
            extraction_multiplier = 5 if (filter_text or filter_duplicates) else 2
            candidate_count = max_frames * extraction_multiplier

            # Ensure minimum time separation between candidate frames
            min_frame_interval = int(min_time_separation * video_fps)
            frame_indices = []
            for i in range(candidate_count):
                frame_idx = int(i * total_frames / candidate_count)
                # Only add if it's far enough from the last candidate
                if not frame_indices or (frame_idx - frame_indices[-1]) >= min_frame_interval:
                    frame_indices.append(frame_idx)

            for frame_number in frame_indices:
                if len(frames_data) >= max_frames:
                    break

                # Set position to the specific frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                ret, frame = cap.read()

                if not ret:
                    logger.warning(f"Failed to read frame at position {frame_number}")
                    continue

                timestamp = frame_number / video_fps

                # Check minimum time separation
                if (timestamp - last_accepted_timestamp) < min_time_separation:
                    filtered_count["time_separation"] += 1
                    continue

                # Apply filters
                if filter_text and has_too_much_text(frame):
                    filtered_count["text"] += 1
                    continue

                if filter_text and not is_likely_surgical_content(frame):
                    filtered_count["text"] += 1
                    continue

                if filter_duplicates and is_duplicate_frame(frame, previous_frames):
                    filtered_count["duplicate"] += 1
                    continue

                # Encode frame to base64
                _, buffer = cv2.imencode('.jpg', frame)
                base64_image = base64.b64encode(buffer).decode('utf-8')

                frames_data.append({
                    "timestamp": round(timestamp, 2),
                    "frame_number": frame_number,
                    "base64_image": base64_image,
                    "width": width,
                    "height": height
                })

                # Update last accepted timestamp
                last_accepted_timestamp = timestamp

                # Store frame for duplicate detection
                if filter_duplicates:
                    previous_frames.append(frame)

            logger.info(f"Extracted {len(frames_data)} frames (filtered {filtered_count['text']} text/title, {filtered_count['duplicate']} duplicates, {filtered_count['time_separation']} too close in time)")

        else:
            # Original behavior: extract frames at specified FPS with filtering
            # Ensure the interval respects minimum time separation
            frame_interval = max(int(video_fps / fps), int(min_time_separation * video_fps))
            logger.info(f"Extracting frames every {frame_interval} frames ({frame_interval/video_fps:.1f}s, min {min_time_separation}s)")
            frame_count = 0

            while True:
                ret, frame = cap.read()

                if not ret:
                    break

                # Extract frame at specified interval
                if frame_count % frame_interval == 0:
                    timestamp = frame_count / video_fps

                    # Check minimum time separation
                    if (timestamp - last_accepted_timestamp) < min_time_separation:
                        filtered_count["time_separation"] += 1
                        frame_count += 1
                        continue

                    # Apply filters
                    skip_frame = False

                    if filter_text and has_too_much_text(frame):
                        filtered_count["text"] += 1
                        skip_frame = True

                    if not skip_frame and filter_text and not is_likely_surgical_content(frame):
                        filtered_count["text"] += 1
                        skip_frame = True

                    if not skip_frame and filter_duplicates and is_duplicate_frame(frame, previous_frames):
                        filtered_count["duplicate"] += 1
                        skip_frame = True

                    if not skip_frame:
                        # Encode frame to base64
                        _, buffer = cv2.imencode('.jpg', frame)
                        base64_image = base64.b64encode(buffer).decode('utf-8')

                        frames_data.append({
                            "timestamp": round(timestamp, 2),
                            "frame_number": frame_count,
                            "base64_image": base64_image,
                            "width": width,
                            "height": height
                        })

                        # Update last accepted timestamp
                        last_accepted_timestamp = timestamp

                        # Store frame for duplicate detection
                        if filter_duplicates:
                            previous_frames.append(frame)

                frame_count += 1

            logger.info(f"Extracted {len(frames_data)} frames at {fps} FPS (filtered {filtered_count['text']} text/title, {filtered_count['duplicate']} duplicates, {filtered_count['time_separation']} too close in time)")

        cap.release()

        return frames_data

    except Exception as e:
        logger.error(f"Error extracting frames: {e}")
        raise


def save_frame_to_file(frame_data: Dict, output_dir: str) -> str:
    """
    Save a base64 frame to a file.

    Args:
        frame_data: Frame data dictionary with base64_image
        output_dir: Directory to save the frame

    Returns:
        Path to saved frame file
    """
    try:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = frame_data["timestamp"]
        filename = f"frame_{timestamp:.2f}s.jpg"
        file_path = output_path / filename

        # Decode and save
        image_bytes = base64.b64decode(frame_data["base64_image"])
        with open(file_path, "wb") as f:
            f.write(image_bytes)

        logger.info(f"Saved frame to: {file_path}")
        return str(file_path)

    except Exception as e:
        logger.error(f"Error saving frame: {e}")
        raise


def get_video_info(video_path: str) -> Dict[str, any]:
    """
    Get video metadata without extracting frames.

    Args:
        video_path: Path to video file

    Returns:
        Dictionary with video information
    """
    try:
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(f"Failed to open video: {video_path}")

        video_info = {
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "duration_seconds": cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS),
            "codec": int(cap.get(cv2.CAP_PROP_FOURCC)),
        }

        cap.release()

        return video_info

    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        raise
