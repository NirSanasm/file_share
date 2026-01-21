"""
Storage abstraction layer supporting GCS and local filesystem.
"""
import os
import shutil
from abc import ABC, abstractmethod
from typing import Tuple, Optional, List
from fastapi import UploadFile

from config import STORAGE_BACKEND, GCS_BUCKET_NAME, LOCAL_UPLOAD_DIR


class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def upload_file(self, filename: str, content: bytes, content_type: str) -> str:
        """Upload binary content and return public URL."""
        pass
    
    @abstractmethod
    def upload_text(self, filename: str, text: str) -> str:
        """Upload text content and return public URL."""
        pass
    
    @abstractmethod
    def get_file_content(self, filename: str) -> Tuple[Optional[str], str]:
        """Get file content. Returns (content, type) where type is 'text' or 'binary'."""
        pass
    
    @abstractmethod
    def list_files(self, prefix: str = "") -> List[str]:
        """List all files, optionally filtered by prefix."""
        pass
    
    @abstractmethod
    def file_exists(self, prefix: str) -> Optional[str]:
        """Check if a file starting with prefix exists. Returns filename if found."""
        pass
    
    @abstractmethod
    def get_public_url(self, filename: str) -> str:
        """Get the public URL for a file."""
        pass


class LocalStorage(StorageBackend):
    """Local filesystem storage backend."""
    
    def __init__(self):
        self.upload_dir = LOCAL_UPLOAD_DIR
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)
    
    def upload_file(self, filename: str, content: bytes, content_type: str) -> str:
        filepath = os.path.join(self.upload_dir, filename)
        with open(filepath, "wb") as f:
            f.write(content)
        return f"/uploads/{filename}"
    
    def upload_text(self, filename: str, text: str) -> str:
        filepath = os.path.join(self.upload_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)
        return f"/uploads/{filename}"
    
    def get_file_content(self, filename: str) -> Tuple[Optional[str], str]:
        filepath = os.path.join(self.upload_dir, filename)
        if not os.path.exists(filepath):
            return None, "none"
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read(), "text"
        except UnicodeDecodeError:
            return f"/uploads/{filename}", "binary"
    
    def list_files(self, prefix: str = "") -> List[str]:
        if not os.path.exists(self.upload_dir):
            return []
        files = os.listdir(self.upload_dir)
        if prefix:
            files = [f for f in files if f.startswith(prefix)]
        return files
    
    def file_exists(self, prefix: str) -> Optional[str]:
        for f in self.list_files():
            if f.startswith(prefix + ".") or f == prefix:
                return f
        return None
    
    def get_public_url(self, filename: str) -> str:
        return f"/uploads/{filename}"


class GCSStorage(StorageBackend):
    """Google Cloud Storage backend."""
    
    def __init__(self):
        from google.cloud import storage
        self.client = storage.Client()
        self.bucket = self.client.bucket(GCS_BUCKET_NAME)
    
    def upload_file(self, filename: str, content: bytes, content_type: str) -> str:
        blob = self.bucket.blob(filename)
        blob.upload_from_string(content, content_type=content_type)
        blob.make_public()
        return blob.public_url
    
    def upload_text(self, filename: str, text: str) -> str:
        blob = self.bucket.blob(filename)
        blob.upload_from_string(text.encode("utf-8"), content_type="text/plain")
        blob.make_public()
        return blob.public_url
    
    def get_file_content(self, filename: str) -> Tuple[Optional[str], str]:
        blob = self.bucket.blob(filename)
        if not blob.exists():
            return None, "none"
        
        # Try to read as text first
        try:
            content = blob.download_as_text(encoding="utf-8")
            return content, "text"
        except UnicodeDecodeError:
            return blob.public_url, "binary"
    
    def list_files(self, prefix: str = "") -> List[str]:
        blobs = self.client.list_blobs(GCS_BUCKET_NAME, prefix=prefix)
        return [blob.name for blob in blobs]
    
    def file_exists(self, prefix: str) -> Optional[str]:
        # Check for files starting with the prefix
        blobs = list(self.client.list_blobs(GCS_BUCKET_NAME, prefix=prefix, max_results=10))
        for blob in blobs:
            if blob.name.startswith(prefix + ".") or blob.name == prefix:
                return blob.name
        return None
    
    def get_public_url(self, filename: str) -> str:
        blob = self.bucket.blob(filename)
        return blob.public_url


def get_storage() -> StorageBackend:
    """Get the configured storage backend."""
    if STORAGE_BACKEND == "gcs":
        if not GCS_BUCKET_NAME:
            raise ValueError("GCS_BUCKET_NAME environment variable is required for GCS storage")
        return GCSStorage()
    return LocalStorage()


# Global storage instance
storage = get_storage()
