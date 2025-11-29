#!/usr/bin/env python
"""
Simple script to test API connectivity and Firebase configuration.
Run this after setting up your environment to verify everything is configured correctly.
"""

import sys
import os
from pathlib import Path

def test_environment_vars():
    """Test that required environment variables are set."""
    print("🔍 Checking environment variables...")

    required_vars = {
        "FIREBASE_CREDENTIALS": "Path to Firebase credentials JSON"
    }

    optional_vars = {
        "API_HOST": "API host (default: 0.0.0.0)",
        "API_PORT": "API port (default: 8000)",
        "ALLOWED_ORIGINS": "CORS origins",
    }

    missing = []
    for var, desc in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: {value}")
        else:
            print(f"  ❌ {var}: NOT SET ({desc})")
            missing.append(var)

    print("\n  Optional variables:")
    for var, desc in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: {value}")
        else:
            print(f"  ⚠️  {var}: Using default ({desc})")

    return len(missing) == 0


def test_firebase_credentials():
    """Test that Firebase credentials file exists."""
    print("\n🔍 Checking Firebase credentials...")

    cred_path = os.getenv('FIREBASE_CREDENTIALS', './firebase-credentials.json')

    if Path(cred_path).exists():
        print(f"  ✅ Credentials file found: {cred_path}")
        return True
    else:
        print(f"  ❌ Credentials file NOT found: {cred_path}")
        print("     Download from Firebase Console → Project Settings → Service Accounts")
        return False


def test_upload_directory():
    """Test that upload directory exists or can be created."""
    print("\n🔍 Checking upload directory...")

    upload_dir = Path("uploads/videos")

    try:
        upload_dir.mkdir(parents=True, exist_ok=True)
        print(f"  ✅ Upload directory ready: {upload_dir}")
        return True
    except Exception as e:
        print(f"  ❌ Cannot create upload directory: {e}")
        return False


def test_imports():
    """Test that required packages can be imported."""
    print("\n🔍 Checking Python dependencies...")

    packages = {
        "fastapi": "FastAPI framework",
        "uvicorn": "ASGI server",
        "firebase_admin": "Firebase Admin SDK",
        "google.cloud.storage": "Google Cloud Storage",
        "google.cloud.firestore": "Google Cloud Firestore",
    }

    missing = []
    for package, desc in packages.items():
        try:
            __import__(package)
            print(f"  ✅ {package}: Installed")
        except ImportError:
            print(f"  ❌ {package}: NOT installed ({desc})")
            missing.append(package)

    if missing:
        print(f"\n  Install missing packages with: pip install -e .")
        return False

    return True


def test_api_server():
    """Check if API server is running."""
    print("\n🔍 Checking API server...")

    try:
        import httpx

        api_url = os.getenv('REACT_APP_API_URL', 'http://localhost:8000')

        try:
            response = httpx.get(f"{api_url}/health", timeout=2.0)
            if response.status_code == 200:
                print(f"  ✅ API server is running: {api_url}")
                print(f"     Response: {response.json()}")
                return True
            else:
                print(f"  ⚠️  API server responded with status {response.status_code}")
                return False
        except httpx.ConnectError:
            print(f"  ⚠️  API server not running at {api_url}")
            print("     Start with: python -m uvicorn src.docuhelp.ui.api.main:app --reload")
            return False

    except ImportError:
        print("  ⚠️  httpx not installed (optional test)")
        return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("DocuHelp API Configuration Test")
    print("=" * 60)

    # Load .env file if python-dotenv is available
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded .env file\n")
    except ImportError:
        print("⚠️  python-dotenv not installed, using system environment\n")

    results = {
        "Environment Variables": test_environment_vars(),
        "Firebase Credentials": test_firebase_credentials(),
        "Upload Directory": test_upload_directory(),
        "Python Dependencies": test_imports(),
        "API Server": test_api_server(),
    }

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test}")

    print("\n" + "=" * 60)

    all_passed = all(results.values())

    if all_passed:
        print("🎉 All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("1. Start backend: python -m uvicorn src.docuhelp.ui.api.main:app --reload")
        print("2. Start frontend: cd frontend && npm start")
        print("3. Open http://localhost:3000")
        return 0
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        print("\nSee QUICK_START.md for setup instructions.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
