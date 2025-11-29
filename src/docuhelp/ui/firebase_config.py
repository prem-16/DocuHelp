"""Firebase configuration and initialization."""
import os
import json
from pathlib import Path
from typing import Optional
import firebase_admin
from firebase_admin import credentials, firestore, storage
import logging

logger = logging.getLogger(__name__)

_firebase_initialized = False
_firestore_client = None
_storage_bucket = None


def initialize_firebase(credentials_path: Optional[str] = None) -> None:
    """
    Initialize Firebase Admin SDK.

    Args:
        credentials_path: Path to Firebase service account JSON file.
                         If not provided, will look for FIREBASE_CREDENTIALS env var
                         or 'firebase-credentials.json' in project root.
    """
    global _firebase_initialized, _firestore_client, _storage_bucket

    if _firebase_initialized:
        logger.info("Firebase already initialized")
        return

    # Determine credentials path
    if credentials_path is None:
        # Check environment variable first
        credentials_path = os.getenv('FIREBASE_CREDENTIALS')

        # Fall back to default location
        if credentials_path is None:
            project_root = Path(__file__).parent.parent.parent.parent
            default_path = project_root / 'firebase-credentials.json'
            if default_path.exists():
                credentials_path = str(default_path)

    # Initialize Firebase
    try:
        if credentials_path and Path(credentials_path).exists():
            logger.info(f"Initializing Firebase with credentials from: {credentials_path}")
            cred = credentials.Certificate(credentials_path)

            # Get storage bucket from credentials
            with open(credentials_path, 'r') as f:
                cred_data = json.load(f)
                project_id = cred_data.get('project_id')
                bucket_name = os.getenv('FIREBASE_STORAGE_BUCKET', f"{project_id}.appspot.com")

            firebase_admin.initialize_app(cred, {
                'storageBucket': bucket_name
            })
        else:
            logger.warning("No Firebase credentials found. Initializing with default credentials.")
            # For development/testing - uses Application Default Credentials
            firebase_admin.initialize_app()

        _firestore_client = firestore.client()
        _storage_bucket = storage.bucket()
        _firebase_initialized = True
        logger.info("Firebase initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        raise


def get_firestore_client():
    """Get Firestore client instance."""
    if not _firebase_initialized:
        initialize_firebase()
    return _firestore_client


def get_storage_bucket():
    """Get Firebase Storage bucket instance."""
    if not _firebase_initialized:
        initialize_firebase()
    return _storage_bucket


def upload_to_storage(
    local_path: str,
    destination_path: str,
    content_type: Optional[str] = None
) -> str:
    """
    Upload a file to Firebase Storage.

    Args:
        local_path: Path to local file
        destination_path: Destination path in Firebase Storage
        content_type: MIME type of the file

    Returns:
        Public URL of uploaded file
    """
    bucket = get_storage_bucket()
    blob = bucket.blob(destination_path)

    # Upload file
    blob.upload_from_filename(local_path, content_type=content_type)

    # Make publicly accessible (optional - adjust based on security requirements)
    # blob.make_public()

    # Generate signed URL (valid for 7 days)
    from datetime import timedelta
    url = blob.generate_signed_url(expiration=timedelta(days=7))

    logger.info(f"File uploaded to: {destination_path}")
    return url


def save_to_firestore(collection: str, document_id: str, data: dict) -> None:
    """
    Save data to Firestore.

    Args:
        collection: Collection name
        document_id: Document ID
        data: Data to save
    """
    db = get_firestore_client()
    db.collection(collection).document(document_id).set(data)
    logger.info(f"Data saved to Firestore: {collection}/{document_id}")


def get_from_firestore(collection: str, document_id: str) -> Optional[dict]:
    """
    Get data from Firestore.

    Args:
        collection: Collection name
        document_id: Document ID

    Returns:
        Document data or None if not found
    """
    db = get_firestore_client()
    doc = db.collection(collection).document(document_id).get()
    return doc.to_dict() if doc.exists else None
