"""
File Storage Utility - AES encryption, folder management, duplicate detection
"""
import os
import hashlib
import shutil
import logging
from pathlib import Path
from datetime import datetime
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class FileEncryption:
    """AES-256 file encryption using Fernet (AES-128-CBC with HMAC)"""

    def __init__(self, encryption_key: str):
        """
        Args:
            encryption_key: Base64-encoded 32-byte key (from config ENCRYPTION_KEY)
        """
        key_bytes = encryption_key.encode()[:32].ljust(32, b'0')
        import base64
        self._fernet = Fernet(base64.urlsafe_b64encode(key_bytes))

    def encrypt_file(self, source_path: str, dest_path: str) -> dict:
        """
        Encrypt file from source_path and write ciphertext to dest_path.
        
        Returns:
            dict: {'success': bool, 'encrypted_size': int}
        """
        try:
            with open(source_path, 'rb') as f:
                plaintext = f.read()
            ciphertext = self._fernet.encrypt(plaintext)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, 'wb') as f:
                f.write(ciphertext)
            return {'success': True, 'encrypted_size': len(ciphertext)}
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            return {'success': False, 'error': str(e)}

    def decrypt_file(self, source_path: str, dest_path: str) -> dict:
        """
        Decrypt ciphertext from source_path and write plaintext to dest_path.
        
        Returns:
            dict: {'success': bool, 'decrypted_size': int}
        """
        try:
            with open(source_path, 'rb') as f:
                ciphertext = f.read()
            plaintext = self._fernet.decrypt(ciphertext)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, 'wb') as f:
                f.write(plaintext)
            return {'success': True, 'decrypted_size': len(plaintext)}
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return {'success': False, 'error': str(e)}

    def decrypt_to_bytes(self, source_path: str) -> bytes | None:
        """Decrypt file and return bytes (for serving downloads)."""
        try:
            with open(source_path, 'rb') as f:
                ciphertext = f.read()
            return self._fernet.decrypt(ciphertext)
        except Exception as e:
            logger.error(f"Decrypt to bytes error: {e}")
            return None


class FileStorage:
    """Manages on-disk storage with user-specific folders and duplicate detection."""

    def __init__(self, upload_root: str, encryption_key: str):
        """
        Args:
            upload_root: Base upload directory (config UPLOAD_FOLDER)
            encryption_key: Key passed to FileEncryption
        """
        self.upload_root = Path(upload_root)
        self.encryption = FileEncryption(encryption_key)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compute_hash(self, file_path: str) -> str:
        """Return SHA-256 hex digest of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def user_folder(self, user_id: int, category: str) -> Path:
        """Return (and create) the user/category subfolder path."""
        folder = self.upload_root / str(user_id) / category
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def store_file(self, tmp_path: str, user_id: int, category: str,
                   original_filename: str) -> dict:
        """
        Encrypt and persist an uploaded file.

        Args:
            tmp_path: Path to the temporary (unencrypted) file
            user_id: Owning user ID
            category: Predicted/selected category (used as sub-folder)
            original_filename: Browser-supplied filename (sanitized by caller)

        Returns:
            dict with keys: success, file_hash, stored_path, file_size, encrypted_size
        """
        try:
            file_hash = self.compute_hash(tmp_path)
            file_size = os.path.getsize(tmp_path)

            # Build deterministic stored name: <timestamp>_<hash8>_<original>
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            safe_name = f"{timestamp}_{file_hash[:8]}_{original_filename}"
            dest_folder = self.user_folder(user_id, category)
            dest_path = dest_folder / safe_name

            result = self.encryption.encrypt_file(tmp_path, str(dest_path))
            if not result['success']:
                return result

            return {
                'success': True,
                'file_hash': file_hash,
                'stored_path': str(dest_path),
                'file_size': file_size,
                'encrypted_size': result['encrypted_size'],
            }
        except Exception as e:
            logger.error(f"store_file error: {e}")
            return {'success': False, 'error': str(e)}

    def store_file_flat(self, tmp_path: str, user_id: int, file_id: int) -> dict:
        """
        Encrypt and store a file at uploads/{user_id}/storage/{file_id}.enc.

        No semantic information (category, filename) is encoded in the path —
        the path is derived solely from the owning user and the document's DB id.

        Args:
            tmp_path:  Path to the temporary (unencrypted) file.
            user_id:   Owning user ID.
            file_id:   Document.id (must already be assigned via DB flush).

        Returns:
            dict with keys: success, file_hash, stored_path, file_size, encrypted_size
        """
        try:
            file_hash = self.compute_hash(tmp_path)
            file_size = os.path.getsize(tmp_path)

            dest_folder = self.upload_root / str(user_id) / 'storage'
            dest_folder.mkdir(parents=True, exist_ok=True)
            dest_path = dest_folder / f"{file_id}.enc"

            result = self.encryption.encrypt_file(tmp_path, str(dest_path))
            if not result['success']:
                return result

            return {
                'success': True,
                'file_hash': file_hash,
                'stored_path': str(dest_path),
                'file_size': file_size,
                'encrypted_size': result['encrypted_size'],
            }
        except Exception as e:
            logger.error(f"store_file_flat error: {e}")
            return {'success': False, 'error': str(e)}

    def move_file(self, current_path: str, user_id: int,
                  new_category: str) -> dict:
        """
        Deprecated: flat storage means files never move on disk.
        Category changes are DB-only; the physical file stays at
        uploads/{user_id}/storage/{doc_id}.enc.

        Returns success immediately to preserve backward compat with any
        callers that still reference this method.
        """
        return {'success': True, 'new_path': current_path}

    def delete_file(self, file_path: str) -> dict:
        """
        Permanently remove a stored file from disk.

        Returns:
            dict with keys: success
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
            return {'success': True}
        except Exception as e:
            logger.error(f"delete_file error: {e}")
            return {'success': False, 'error': str(e)}

    def get_decrypted_bytes(self, file_path: str) -> bytes | None:
        """Return plaintext bytes of an encrypted stored file (for download)."""
        return self.encryption.decrypt_to_bytes(file_path)
