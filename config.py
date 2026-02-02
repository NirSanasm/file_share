import os
from dotenv import load_dotenv

load_dotenv()

# Storage backend: "gcs" or "local"
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")

# Google Cloud Storage settings
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "")
GCS_CREDENTIALS_JSON = os.getenv("GCS_CREDENTIALS_JSON")

# Local storage directory (fallback)
LOCAL_UPLOAD_DIR = "uploads"

# Google reCAPTCHA settings
RECAPTCHA_SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY", "")
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY", "")
