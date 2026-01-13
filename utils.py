import random
import string
import os
import shutil
from fastapi import UploadFile

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def generate_short_id(length=6):
    """Generate a random short ID for pastes."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def save_text_paste(content: str, filename: str):
    """Save text content to a file."""
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath

async def save_upload_file(upload_file: UploadFile, filename: str):
    """Save an uploaded file to disk."""
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return filepath

def get_file_content(filename: str):
    """Read content from a file."""
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        return None
    
    # Try reading as text first
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read(), "text"
    except UnicodeDecodeError:
        return filepath, "binary" # Return path for binary/image files
