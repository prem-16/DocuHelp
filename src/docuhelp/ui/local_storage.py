"""
Local storage module for metadata when Firebase is not used.
Stores video metadata in JSON files.
"""
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Storage directory for metadata
METADATA_DIR = Path("frontend/uploads/metadata")
METADATA_DIR.mkdir(parents=True, exist_ok=True)


def save_metadata(video_id: str, data: Dict[str, Any]) -> None:
    """
    Save video metadata to local JSON file.

    Args:
        video_id: Unique video identifier
        data: Metadata dictionary to save
    """
    try:
        metadata_file = METADATA_DIR / f"{video_id}.json"

        # Add timestamp if not present
        if "saved_at" not in data:
            data["saved_at"] = datetime.utcnow().isoformat()

        with open(metadata_file, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Metadata saved locally: {metadata_file}")

    except Exception as e:
        logger.error(f"Error saving metadata: {e}")
        raise


def get_metadata(video_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve video metadata from local JSON file.

    Args:
        video_id: Unique video identifier

    Returns:
        Metadata dictionary or None if not found
    """
    try:
        metadata_file = METADATA_DIR / f"{video_id}.json"

        if not metadata_file.exists():
            logger.warning(f"Metadata not found: {video_id}")
            return None

        with open(metadata_file, "r") as f:
            data = json.load(f)

        logger.info(f"Metadata retrieved: {video_id}")
        return data

    except Exception as e:
        logger.error(f"Error retrieving metadata: {e}")
        return None


def update_metadata(video_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update existing metadata with new fields.

    Args:
        video_id: Unique video identifier
        updates: Dictionary of fields to update

    Returns:
        True if successful, False otherwise
    """
    try:
        existing = get_metadata(video_id)
        if not existing:
            logger.error(f"Cannot update non-existent metadata: {video_id}")
            return False

        # Merge updates
        existing.update(updates)
        existing["updated_at"] = datetime.utcnow().isoformat()

        save_metadata(video_id, existing)
        return True

    except Exception as e:
        logger.error(f"Error updating metadata: {e}")
        return False


def list_all_videos() -> list:
    """
    List all video IDs in local storage.

    Returns:
        List of video IDs
    """
    try:
        video_ids = []
        for file in METADATA_DIR.glob("*.json"):
            video_ids.append(file.stem)
        return video_ids

    except Exception as e:
        logger.error(f"Error listing videos: {e}")
        return []


def delete_metadata(video_id: str) -> bool:
    """
    Delete metadata file.

    Args:
        video_id: Unique video identifier

    Returns:
        True if successful, False otherwise
    """
    try:
        metadata_file = METADATA_DIR / f"{video_id}.json"

        if metadata_file.exists():
            metadata_file.unlink()
            logger.info(f"Metadata deleted: {video_id}")
            return True
        else:
            logger.warning(f"Metadata not found for deletion: {video_id}")
            return False

    except Exception as e:
        logger.error(f"Error deleting metadata: {e}")
        return False
