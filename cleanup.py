"""
Auto-cleanup service for managing file expiration and storage quotas.
"""
import os
import time
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
from pathlib import Path
from storage import storage
from config import LOCAL_UPLOAD_DIR

# Configuration
FILE_EXPIRATION_DAYS = 7  # Files expire after 7 days
CLEANUP_INTERVAL = 3600  # Run cleanup every hour (in seconds)
METADATA_FILE = "file_metadata.json"
MAX_STORAGE_PER_IP_MB = 100  # 100MB per IP address


class FileMetadata:
    """Manages metadata for uploaded files."""
    
    def __init__(self, metadata_path: str = None):
        if metadata_path is None:
            metadata_path = os.path.join(LOCAL_UPLOAD_DIR, METADATA_FILE)
        self.metadata_path = metadata_path
        self.metadata: Dict = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Load metadata from JSON file."""
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {'files': {}, 'ip_usage': {}}
        return {'files': {}, 'ip_usage': {}}
    
    def _save_metadata(self):
        """Save metadata to JSON file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.metadata_path), exist_ok=True)
            with open(self.metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except IOError as e:
            print(f"Failed to save metadata: {e}")
    
    def add_file(self, filename: str, ip: str, size_bytes: int):
        """Add file metadata."""
        current_time = datetime.now().isoformat()
        
        self.metadata['files'][filename] = {
            'uploaded_at': current_time,
            'ip': ip,
            'size_bytes': size_bytes,
            'expires_at': (datetime.now() + timedelta(days=FILE_EXPIRATION_DAYS)).isoformat()
        }
        
        # Update IP usage
        if ip not in self.metadata['ip_usage']:
            self.metadata['ip_usage'][ip] = {'total_bytes': 0, 'file_count': 0}
        
        self.metadata['ip_usage'][ip]['total_bytes'] += size_bytes
        self.metadata['ip_usage'][ip]['file_count'] += 1
        
        self._save_metadata()
    
    def remove_file(self, filename: str):
        """Remove file metadata."""
        if filename in self.metadata['files']:
            file_info = self.metadata['files'][filename]
            ip = file_info['ip']
            size_bytes = file_info['size_bytes']
            
            # Update IP usage
            if ip in self.metadata['ip_usage']:
                self.metadata['ip_usage'][ip]['total_bytes'] -= size_bytes
                self.metadata['ip_usage'][ip]['file_count'] -= 1
                
                # Remove IP entry if no files left
                if self.metadata['ip_usage'][ip]['file_count'] <= 0:
                    del self.metadata['ip_usage'][ip]
            
            del self.metadata['files'][filename]
            self._save_metadata()
    
    def get_file_info(self, filename: str) -> Optional[Dict]:
        """Get metadata for a specific file."""
        return self.metadata['files'].get(filename)
    
    def get_ip_usage(self, ip: str) -> Dict:
        """Get storage usage for an IP address."""
        return self.metadata['ip_usage'].get(ip, {'total_bytes': 0, 'file_count': 0})
    
    def check_ip_quota(self, ip: str, new_file_size: int) -> tuple[bool, str]:
        """
        Check if IP has quota for new file.
        Returns (is_allowed, error_message)
        """
        usage = self.get_ip_usage(ip)
        current_mb = usage['total_bytes'] / (1024 * 1024)
        new_file_mb = new_file_size / (1024 * 1024)
        
        if current_mb + new_file_mb > MAX_STORAGE_PER_IP_MB:
            return False, f"Storage quota exceeded. You have used {current_mb:.2f}MB of {MAX_STORAGE_PER_IP_MB}MB. This file would exceed your limit."
        
        return True, ""
    
    def get_expired_files(self) -> list:
        """Get list of expired files."""
        current_time = datetime.now()
        expired = []
        
        for filename, info in self.metadata['files'].items():
            expires_at = datetime.fromisoformat(info['expires_at'])
            if current_time > expires_at:
                expired.append(filename)
        
        return expired
    
    def get_all_files(self) -> Dict:
        """Get all file metadata."""
        return self.metadata['files']


class CleanupService:
    """Background service for cleaning up expired files."""
    
    def __init__(self):
        self.metadata = FileMetadata()
        self.is_running = False
    
    async def cleanup_expired_files(self):
        """Remove expired files from storage."""
        expired_files = self.metadata.get_expired_files()
        
        if not expired_files:
            print(f"[Cleanup] No expired files found at {datetime.now()}")
            return
        
        print(f"[Cleanup] Found {len(expired_files)} expired files")
        
        for filename in expired_files:
            try:
                # Delete file from storage
                filepath = os.path.join(LOCAL_UPLOAD_DIR, filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
                    print(f"[Cleanup] Deleted expired file: {filename}")
                
                # Remove from metadata
                self.metadata.remove_file(filename)
            except Exception as e:
                print(f"[Cleanup] Failed to delete {filename}: {e}")
    
    async def cleanup_orphaned_files(self):
        """Remove files that exist in storage but not in metadata."""
        if not os.path.exists(LOCAL_UPLOAD_DIR):
            return
        
        # Get all files in storage
        storage_files = set(os.listdir(LOCAL_UPLOAD_DIR))
        storage_files.discard(METADATA_FILE)  # Exclude metadata file
        
        # Get all files in metadata
        metadata_files = set(self.metadata.get_all_files().keys())
        
        # Find orphaned files
        orphaned = storage_files - metadata_files
        
        if orphaned:
            print(f"[Cleanup] Found {len(orphaned)} orphaned files")
            for filename in orphaned:
                try:
                    filepath = os.path.join(LOCAL_UPLOAD_DIR, filename)
                    # Only delete if file is older than 1 day (safety measure)
                    if os.path.exists(filepath):
                        file_age = time.time() - os.path.getmtime(filepath)
                        if file_age > 86400:  # 1 day
                            os.remove(filepath)
                            print(f"[Cleanup] Deleted orphaned file: {filename}")
                except Exception as e:
                    print(f"[Cleanup] Failed to delete orphaned file {filename}: {e}")
    
    async def run_cleanup_loop(self):
        """Main cleanup loop that runs periodically."""
        self.is_running = True
        print(f"[Cleanup] Service started. Running every {CLEANUP_INTERVAL} seconds")
        
        while self.is_running:
            try:
                await self.cleanup_expired_files()
                await self.cleanup_orphaned_files()
            except Exception as e:
                print(f"[Cleanup] Error during cleanup: {e}")
            
            # Wait for next cleanup interval
            await asyncio.sleep(CLEANUP_INTERVAL)
    
    def stop(self):
        """Stop the cleanup service."""
        self.is_running = False
        print("[Cleanup] Service stopped")


# Global cleanup service instance
cleanup_service = CleanupService()
file_metadata = FileMetadata()
