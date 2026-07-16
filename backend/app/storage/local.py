"""
Local filesystem storage interface implementation.
"""
import hashlib
import os
from typing import Tuple
from uuid import UUID
from fastapi import UploadFile
from app.core.config import settings


class LocalStorageService:
    """
    Manages local filesystem storage, handling file streaming, checksum updates, and directory creation.
    """
    def __init__(self):
        # Auto-create uploads directories on initialization
        os.makedirs(settings.RAW_UPLOAD_DIR, exist_ok=True)
        os.makedirs(settings.CLEANED_UPLOAD_DIR, exist_ok=True)

    def save_upload(
        self,
        upload_file: UploadFile,
        user_id: UUID,
        dataset_id: UUID,
        version: int,
        ext: str,
        subfolder: str = "raw"
    ) -> Tuple[str, int, str]:
        """
        Streams file upload to disk in chunks, calculates the SHA256 hash dynamically,
        and returns (storage_path, file_size, sha256_checksum).
        """
        user_dir = os.path.join(settings.STORAGE_ROOT, subfolder, str(user_id), str(dataset_id))
        os.makedirs(user_dir, exist_ok=True)
        
        filename = f"version_{version}{ext}"
        destination_path = os.path.join(user_dir, filename)
        
        sha256_hash = hashlib.sha256()
        file_size = 0
        chunk_size = 1024 * 1024  # 1MB chunks
        
        with open(destination_path, "wb") as buffer:
            # Reset file pointer to start
            upload_file.file.seek(0)
            while True:
                chunk = upload_file.file.read(chunk_size)
                if not chunk:
                    break
                buffer.write(chunk)
                sha256_hash.update(chunk)
                file_size += len(chunk)
                
        # Generate generic schema identifier (local://...)
        normalized_path = destination_path.replace("\\", "/")
        storage_path = f"local://{normalized_path}"
        
        return storage_path, file_size, sha256_hash.hexdigest()

    def delete_file(self, file_path: str) -> bool:
        """
        Deletes a local file. Accepts local:// prefixed paths or standard paths.
        """
        path = file_path
        if path.startswith("local://"):
            path = path.replace("local://", "", 1)
            
        if os.path.exists(path):
            try:
                os.remove(path)
                return True
            except Exception:
                return False
        return False
