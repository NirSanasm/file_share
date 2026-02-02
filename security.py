"""
Security module for file upload validation and content security.
"""
import os
import re
import magic
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException

# File size limits (in bytes)
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_TEXT_SIZE = 1 * 1024 * 1024    # 1MB
MAX_FILE_SIZE = 10 * 1024 * 1024   # 10MB default

# Allowed file extensions and MIME types
ALLOWED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'}
ALLOWED_TEXT_EXTENSIONS = {'.txt', '.md', '.json', '.xml', '.csv', '.log'}
ALLOWED_CODE_EXTENSIONS = {'.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.go', '.rs', '.ts', '.jsx', '.tsx'}

ALLOWED_MIME_TYPES = {
    # Images
    'image/png', 'image/jpeg', 'image/gif', 'image/webp', 'image/bmp',
    # Text
    'text/plain', 'text/markdown', 'text/csv', 'text/html', 'text/css',
    'application/json', 'application/xml', 'text/xml',
    # Code
    'application/javascript', 'text/javascript', 'application/x-python',
}

# Dangerous file extensions to block
BLOCKED_EXTENSIONS = {
    '.exe', '.dll', '.bat', '.cmd', '.sh', '.ps1', '.msi', '.app',
    '.deb', '.rpm', '.dmg', '.pkg', '.run', '.bin', '.com', '.scr',
    '.vbs', '.jar', '.apk', '.ipa'
}

# Magic bytes for common file types (first few bytes)
MAGIC_BYTES = {
    'image/png': b'\x89PNG\r\n\x1a\n',
    'image/jpeg': b'\xff\xd8\xff',
    'image/gif': b'GIF87a',
    'image/webp': b'RIFF',
    'image/bmp': b'BM',
}


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and other attacks.
    """
    # Remove any path components
    filename = os.path.basename(filename)
    
    # Remove any non-alphanumeric characters except dots, hyphens, and underscores
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    # Prevent hidden files
    if filename.startswith('.'):
        filename = '_' + filename[1:]
    
    # Limit filename length
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    
    return name + ext


def validate_file_extension(filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate file extension against whitelist and blacklist.
    Returns (is_valid, error_message)
    """
    ext = os.path.splitext(filename)[1].lower()
    
    # Check if extension is blocked
    if ext in BLOCKED_EXTENSIONS:
        return False, f"File type '{ext}' is not allowed for security reasons"
    
    # Check if extension is in allowed list
    all_allowed = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_TEXT_EXTENSIONS | ALLOWED_CODE_EXTENSIONS
    if ext and ext not in all_allowed:
        return False, f"File type '{ext}' is not supported. Allowed types: images, text, and code files"
    
    return True, None


def validate_file_size(content: bytes, filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate file size based on file type.
    Returns (is_valid, error_message)
    """
    size = len(content)
    ext = os.path.splitext(filename)[1].lower()
    
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        if size > MAX_IMAGE_SIZE:
            return False, f"Image file too large. Maximum size: {MAX_IMAGE_SIZE // (1024*1024)}MB"
    elif ext in ALLOWED_TEXT_EXTENSIONS or ext in ALLOWED_CODE_EXTENSIONS:
        if size > MAX_TEXT_SIZE:
            return False, f"Text file too large. Maximum size: {MAX_TEXT_SIZE // (1024*1024)}MB"
    else:
        if size > MAX_FILE_SIZE:
            return False, f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
    
    if size == 0:
        return False, "File is empty"
    
    return True, None


def validate_mime_type(content: bytes, filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate MIME type using python-magic (libmagic).
    Returns (is_valid, error_message)
    """
    try:
        # Detect MIME type from content
        mime = magic.from_buffer(content, mime=True)
        
        # Check if MIME type is allowed
        if mime not in ALLOWED_MIME_TYPES:
            # Allow text/plain for code files
            if mime.startswith('text/'):
                return True, None
            return False, f"File type '{mime}' is not allowed"
        
        return True, None
    except Exception as e:
        # If magic fails, allow it but log the error
        print(f"MIME type detection failed: {e}")
        return True, None


def validate_magic_bytes(content: bytes, filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate file content matches expected magic bytes for images.
    Returns (is_valid, error_message)
    """
    ext = os.path.splitext(filename)[1].lower()
    
    # Only validate magic bytes for images
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return True, None
    
    # Check magic bytes
    if ext == '.png' and not content.startswith(MAGIC_BYTES['image/png']):
        return False, "File claims to be PNG but content doesn't match"
    elif ext in ['.jpg', '.jpeg'] and not content.startswith(MAGIC_BYTES['image/jpeg']):
        return False, "File claims to be JPEG but content doesn't match"
    elif ext == '.gif' and not content.startswith(MAGIC_BYTES['image/gif']):
        return False, "File claims to be GIF but content doesn't match"
    elif ext == '.webp' and not content.startswith(MAGIC_BYTES['image/webp']):
        return False, "File claims to be WebP but content doesn't match"
    elif ext == '.bmp' and not content.startswith(MAGIC_BYTES['image/bmp']):
        return False, "File claims to be BMP but content doesn't match"
    
    return True, None


def validate_text_content(text: str) -> Tuple[bool, Optional[str]]:
    """
    Validate text content for size and basic filtering.
    Returns (is_valid, error_message)
    """
    if not text or len(text.strip()) == 0:
        return False, "Text content is empty"
    
    # Check text size
    text_bytes = text.encode('utf-8')
    if len(text_bytes) > MAX_TEXT_SIZE:
        return False, f"Text content too large. Maximum size: {MAX_TEXT_SIZE // (1024*1024)}MB"
    
    # Basic spam detection (too many repeated characters)
    if len(set(text)) < 5 and len(text) > 100:
        return False, "Text content appears to be spam"
    
    return True, None


async def validate_upload_file(file: UploadFile) -> Tuple[bool, Optional[str], bytes]:
    """
    Comprehensive file validation.
    Returns (is_valid, error_message, file_content)
    """
    if not file or not file.filename:
        return False, "No file provided", b''
    
    # Sanitize filename
    original_filename = file.filename
    sanitized_filename = sanitize_filename(original_filename)
    
    # Validate extension
    is_valid, error = validate_file_extension(sanitized_filename)
    if not is_valid:
        return False, error, b''
    
    # Read file content
    try:
        content = await file.read()
    except Exception as e:
        return False, f"Failed to read file: {str(e)}", b''
    
    # Validate file size
    is_valid, error = validate_file_size(content, sanitized_filename)
    if not is_valid:
        return False, error, b''
    
    # Validate MIME type
    is_valid, error = validate_mime_type(content, sanitized_filename)
    if not is_valid:
        return False, error, b''
    
    # Validate magic bytes for images
    is_valid, error = validate_magic_bytes(content, sanitized_filename)
    if not is_valid:
        return False, error, b''
    
    return True, None, content


def get_file_category(filename: str) -> str:
    """
    Determine file category based on extension.
    """
    ext = os.path.splitext(filename)[1].lower()
    
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        return 'image'
    elif ext in ALLOWED_TEXT_EXTENSIONS:
        return 'text'
    elif ext in ALLOWED_CODE_EXTENSIONS:
        return 'code'
    else:
        return 'unknown'
