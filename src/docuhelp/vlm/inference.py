"""
VLM Inference Pipeline
Processes uploaded videos and runs OpenRouter VLM inference.
"""
import logging
from pathlib import Path
from typing import Dict, Optional, List
import json
import re

from docuhelp.vlm.video_processor import extract_frames_from_video, get_video_info
from docuhelp.vlm.openrouter_client import create_vlm_client
from docuhelp.ui.local_storage import get_metadata, update_metadata

logger = logging.getLogger(__name__)


def run_vlm_inference_pipeline(
    video_id: str,
    fps: int = 1,
    max_frames: Optional[int] = None,
    min_time_separation: float = 30.0
) -> Dict[str, any]:
    """
    Complete VLM inference pipeline for uploaded video.

    Steps:
    1. Get video metadata from local storage
    2. Extract frames from video (1 fps)
    3. Send frames to OpenRouter VLM (Gemini)
    4. Parse response and extract timestamps
    5. Save results back to metadata
    6. Return processed results with key frames

    Args:
        video_id: Video ID from upload
        fps: Frames per second to extract (default: 1)
        max_frames: Maximum frames to extract (None for all)
        min_time_separation: Minimum time separation between frames in seconds (default: 30.0)

    Returns:
        Dictionary with:
        {
            "video_id": "abc-123",
            "procedure": "Laparoscopic Cholecystectomy",
            "summary": "VLM response text",
            "phases": [
                {
                    "timestamp_range": "0:00-0:45",
                    "description": "Initial incision...",
                    "key_timestamp": "0:23",
                    "key_frame_data": "base64_image..."
                },
                ...
            ],
            "latency": 5.2,
            "frames_analyzed": 120
        }
    """
    try:
        logger.info(f"Starting VLM inference pipeline for video: {video_id}")

        # Step 1: Get video metadata
        metadata = get_metadata(video_id)
        if not metadata:
            raise ValueError(f"Video metadata not found: {video_id}")

        video_path = metadata["local_path"]
        procedure = metadata.get("procedure", "Unknown")

        logger.info(f"Processing video: {video_path}, Procedure: {procedure}")

        # Get video duration to scale frame extraction
        video_info = get_video_info(video_path)
        video_duration = video_info.get("duration_seconds", 0)
        logger.info(f"Video duration: {video_duration:.1f}s")

        # Calculate max frames based on video duration
        # Goal: At least 1 phase per 2 minutes (120 seconds)
        # With min_time_separation of 45s, we need enough frames to cover the video
        if max_frames is None:
            # Calculate frames needed: video duration / desired phase interval
            # We want phases every ~2 minutes, so need frames every ~45-60 seconds
            calculated_max_frames = max(6, int(video_duration / 30))  # 1 frame per 30s minimum
            # Cap at 20 to avoid overwhelming the VLM
            max_frames = min(20, calculated_max_frames)
            logger.info(f"Calculated max_frames: {max_frames} for {video_duration:.1f}s video")

        # Step 2: Extract frames with better separation
        logger.info(f"Extracting up to {max_frames} frames at {fps} FPS (min {min_time_separation}s apart)...")
        frames = extract_frames_from_video(
            video_path,
            fps=fps,
            max_frames=max_frames,
            min_time_separation=min_time_separation
        )



        logger.info(f"Extracted {len(frames)} frames")

        # Step 3: Run VLM inference
        logger.info("Running VLM inference with OpenRouter...")
        vlm_client = create_vlm_client()
        vlm_result = vlm_client.analyze_video_frames(frames, procedure=procedure)

        logger.info(f"VLM inference completed in {vlm_result['latency']}s")

        # Step 4: Parse VLM response to extract phases and timestamps
        logger.info(f"VLM summary: {vlm_result['summary']}")
        phases = parse_vlm_response(vlm_result["summary"], frames)
        logger.info(f"Parsed {len(phases)} phases from VLM response")
        # Step 5: Update metadata with results
        update_metadata(video_id, {
            "vlm_summary": vlm_result["summary"],
            "vlm_phases": phases,
            "vlm_latency": vlm_result["latency"],
            "processed": True,
            "status": "completed"
        })

        logger.info(f"VLM inference pipeline completed. Found {len(phases)} phases.")

        # Step 6: Return results
        return {
            "video_id": video_id,
            "procedure": procedure,
            "summary": vlm_result["summary"],
            "phases": phases,
            "latency": vlm_result["latency"],
            "frames_analyzed": len(frames),
            "model": vlm_result["model"]
        }

    except Exception as e:
        logger.error(f"Error in VLM inference pipeline: {e}")

        # Update metadata with error status
        try:
            update_metadata(video_id, {
                "status": "error",
                "error_message": str(e),
                "processed": False
            })
        except:
            pass

        raise


def parse_vlm_response(summary_text: str, frames: List[Dict]) -> List[Dict]:
    """
    Parse VLM response to extract phases with timestamps.

    Args:
        summary_text: Raw VLM response
        frames: List of frames with timestamps

    Returns:
        List of phases with extracted information
    """
    try:
        phases = []
        used_frame_indices = set()  # Track used frames to ensure uniqueness

        # Remove any conversational preamble (e.g., "Okay, I'm ready...")
        clean_text = summary_text
        # Remove common preamble patterns
        preamble_patterns = [
            r'^.*?(?=\*\*PROCEDURE)',  # Everything before first **PROCEDURE or **SURGICAL
            r'^Okay[,.].*?(?=\n)',
            r'^I\'m ready.*?(?=\n)',
            r'^Here is.*?(?=\n)',
        ]
        for pattern in preamble_patterns:
            clean_text = re.sub(pattern, '', clean_text, flags=re.DOTALL | re.MULTILINE)

        # Debug: Log the cleaned text to see what we're parsing
        logger.info(f"Parsing VLM response (first 1000 chars): {clean_text[:1000]}")

        # Try to parse structured response
        # Look for patterns like "0:00-0:45" or "00:00-00:45"
        timestamp_pattern = r'(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})'

        # Count how many timestamp patterns exist
        timestamp_matches = re.findall(timestamp_pattern, clean_text)
        logger.info(f"Found {len(timestamp_matches)} timestamp ranges in VLM response: {timestamp_matches}")

        # Section headers to stop collecting phase descriptions
        section_headers = [
            "PROCEDURE OVERVIEW", "SURGICAL PHASES", "CLINICAL OBSERVATIONS",
            "ACCOUNTABILITY MARKERS", "TECHNICAL QUALITY", "PROCEDURE-SPECIFIC"
        ]

        # Split by common delimiters
        lines = clean_text.split('\n')

        current_phase = {}
        in_phase_section = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if we're entering or leaving the SURGICAL PHASES section
            if "**SURGICAL PHASES**" in line:
                in_phase_section = True
                logger.info("Entered SURGICAL PHASES section")
                continue

            # Check if we've hit another major section (stop collecting phases)
            is_section_header = False
            for header in section_headers:
                if f"**{header}**" in line and header != "SURGICAL PHASES":
                    is_section_header = True
                    in_phase_section = False
                    break

            if is_section_header:
                # Save current phase before moving to next section
                if current_phase and current_phase.get("description"):
                    phases.append(current_phase)
                    current_phase = {}
                continue

            # Look for timestamp range (only in surgical phases section)
            timestamp_match = re.search(timestamp_pattern, line)

            if timestamp_match and in_phase_section:
                # Save previous phase if exists
                if current_phase and current_phase.get("description"):
                    phases.append(current_phase)
                    logger.info(f"Saved phase: {current_phase['timestamp_range']}")

                # Start new phase
                start_min, start_sec, end_min, end_sec = timestamp_match.groups()
                start_time = int(start_min) * 60 + int(start_sec)
                end_time = int(end_min) * 60 + int(end_sec)
                key_time = (start_time + end_time) / 2  # Middle of range

                # Find closest unused frame to key timestamp
                key_frame = find_closest_frame(frames, key_time, used_frame_indices)

                current_phase = {
                    "timestamp_range": timestamp_match.group(0),
                    "start_seconds": start_time,
                    "end_seconds": end_time,
                    "key_timestamp": format_timestamp(key_time),
                    "key_timestamp_seconds": key_time,
                    "key_frame_data": key_frame["base64_image"] if key_frame else None,
                    "description": ""
                }
                logger.info(f"Started new phase: {timestamp_match.group(0)}")

            elif current_phase and line and in_phase_section:
                # Skip numbered list markers (1., 2., 3.) and sub-headers
                if re.match(r'^\d+\.\s*\*\*', line):
                    continue
                if line.startswith("**") and line.endswith("**"):
                    continue

                # Add to description
                # Remove common prefixes and unwanted labels
                clean_line = line
                # Remove bullets, numbers, asterisks
                clean_line = re.sub(r'^[\d\.\-\*\#\>\s]+', '', clean_line)
                # Remove various label patterns
                clean_line = re.sub(r'^\**(Description|Key timestamp|Key time stamp|Timestamp|Phase description)\*{0,2}:?\s*', '', clean_line, flags=re.IGNORECASE)
                # Remove timestamp patterns like "0:08" at the start
                clean_line = re.sub(r'^\d{1,2}:\d{2}\s*', '', clean_line)

                if clean_line.strip():
                    if current_phase["description"]:
                        current_phase["description"] += " " + clean_line.strip()
                    else:
                        current_phase["description"] = clean_line.strip()

        # Add last phase
        if current_phase and current_phase.get("description"):
            phases.append(current_phase)

        # Post-process descriptions to make them more readable
        for phase in phases:
            if phase.get("description"):
                # Clean up any remaining formatting artifacts
                desc = phase["description"]

                # Remove timestamp patterns that leaked into descriptions
                # Pattern 1: M:SS-M:SS (e.g., "0:01-0:03", "1:20-1:45") - most specific first
                desc = re.sub(r'\s*\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\s*', ' ', desc)
                # Pattern 2: :MM-M:SS or similar (e.g., ":01-0:03")
                desc = re.sub(r'\s*:\d{2}\s*-\s*\d{1,2}:\d{2}\s*', ' ', desc)
                # Pattern 3: Standalone timestamps like "0:02" at end or in text
                desc = re.sub(r'\s+\d{1,2}:\d{2}\s*$', '', desc)  # At end
                desc = re.sub(r'^\d{1,2}:\d{2}\s+', '', desc)  # At start
                desc = re.sub(r'\s+\d{1,2}:\d{2}\s+', ' ', desc)  # In middle

                # Remove multiple spaces
                desc = re.sub(r'\s+', ' ', desc)
                # Remove asterisks
                desc = desc.replace('**', '')
                # Remove any remaining orphaned punctuation
                desc = re.sub(r'\s+([.,;:])', r'\1', desc)

                # Capitalize first letter
                if desc:
                    desc = desc[0].upper() + desc[1:] if len(desc) > 1 else desc.upper()

                phase["description"] = desc.strip()

        # If no structured phases found, try alternative parsing or create smart fallback
        if not phases:
            logger.warning("No structured phases found in SURGICAL PHASES section")
            logger.warning(f"VLM response preview: {summary_text[:500]}")
            logger.warning("Attempting fallback: creating phases from available frames")

            # Fallback: Create phases from frames automatically
            # Divide frames into logical groups
            if len(frames) >= 3:
                # Create multiple phases from frames (aim for 3-5 phases)
                num_phases = min(5, max(3, len(frames) // 3))
                frames_per_phase = len(frames) // num_phases

                for i in range(num_phases):
                    start_idx = i * frames_per_phase
                    end_idx = min((i + 1) * frames_per_phase, len(frames))
                    if start_idx >= len(frames):
                        break

                    start_frame = frames[start_idx]
                    end_frame = frames[min(end_idx - 1, len(frames) - 1)]
                    mid_idx = (start_idx + end_idx) // 2
                    key_frame = frames[mid_idx] if mid_idx < len(frames) else frames[start_idx]

                    # Format timestamps
                    start_ts = format_timestamp(start_frame["timestamp"])
                    end_ts = format_timestamp(end_frame["timestamp"])

                    # Extract any description from summary
                    summary_content = extract_general_summary(summary_text)

                    phases.append({
                        "timestamp_range": f"{start_ts}-{end_ts}",
                        "start_seconds": start_frame["timestamp"],
                        "end_seconds": end_frame["timestamp"],
                        "key_timestamp": format_timestamp(key_frame["timestamp"]),
                        "key_timestamp_seconds": key_frame["timestamp"],
                        "key_frame_data": key_frame["base64_image"],
                        "description": f"Surgical procedure phase {i+1}. {summary_content[:100]}"
                    })

                logger.info(f"Created {len(phases)} fallback phases from {len(frames)} frames")
            else:
                # Only create single phase if very few frames
                mid_frame = frames[len(frames) // 2] if frames else None
                summary_content = extract_general_summary(summary_text)
                phases = [{
                    "timestamp_range": "Full video",
                    "description": summary_content,
                    "key_timestamp": format_timestamp(mid_frame["timestamp"]) if mid_frame else "0:00",
                    "key_frame_data": mid_frame["base64_image"] if mid_frame else None
                }]
        else:
            logger.info(f"Successfully parsed {len(phases)} phases with timestamp ranges")

        return phases

    except Exception as e:
        logger.error(f"Error parsing VLM response: {e}")
        # Return raw summary as single phase
        return [{
            "timestamp_range": "Full video",
            "description": summary_text[:500] if len(summary_text) > 500 else summary_text,
            "key_timestamp": "0:00"
        }]


def extract_general_summary(text: str) -> str:
    """Extract a general summary from VLM response if no phases found."""
    lines = text.split('\n')
    summary_parts = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Skip section headers
        if line.startswith('**') and line.endswith('**'):
            continue
        # Skip list markers
        if re.match(r'^[\d\.\-\*\#\>]+\s*$', line):
            continue

        # Clean the line
        clean = re.sub(r'^[\d\.\-\*\#\>\s]+', '', line)
        if len(clean) > 20:  # Only meaningful sentences
            summary_parts.append(clean)
            if len(' '.join(summary_parts)) > 300:  # Limit length
                break

    return ' '.join(summary_parts) if summary_parts else text[:300]


def find_closest_frame(frames: List[Dict], target_seconds: float, used_indices: set = None) -> Optional[Dict]:
    """
    Find frame closest to target timestamp.

    Args:
        frames: List of available frames
        target_seconds: Target timestamp in seconds
        used_indices: Set of already used frame indices to avoid duplicates

    Returns:
        Closest unused frame, or None if no frames available
    """
    if not frames:
        return None

    if used_indices is None:
        used_indices = set()

    # Find all unused frames
    available_frames = [
        (i, f) for i, f in enumerate(frames)
        if i not in used_indices
    ]

    if not available_frames:
        # All frames used, return closest anyway
        closest_frame = min(frames, key=lambda f: abs(f["timestamp"] - target_seconds))
        return closest_frame

    # Find closest unused frame
    closest_idx, closest_frame = min(
        available_frames,
        key=lambda x: abs(x[1]["timestamp"] - target_seconds)
    )

    # Mark this frame as used
    used_indices.add(closest_idx)

    return closest_frame


def format_timestamp(seconds: float) -> str:
    """Format seconds as MM:SS."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"


# Legacy function for compatibility
def run_inference(video_path: str, model: object = None):
    """
    Legacy inference function.
    Use run_vlm_inference_pipeline() for new code.
    """
    logger.warning("run_inference() is deprecated. Use run_vlm_inference_pipeline()")
    print(f"Running inference on {video_path}")
    return []
