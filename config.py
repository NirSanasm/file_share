import os
from dotenv import load_dotenv

load_dotenv()

# Storage backend: "gcs" or "local"
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")

# Google Cloud Storage settings
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "")

# Local storage directory (fallback)
LOCAL_UPLOAD_DIR = "uploads"
