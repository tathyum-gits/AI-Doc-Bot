from cryptography.fernet import Fernet
from typing import Any, Optional, List, Dict
import json
import hashlib
import os
import secrets
from datetime import datetime, timedelta
import base64
from pathlib import Path
import logging
from dataclasses import dataclass
import mimetypes
import time

@dataclass
class FileMetadata:
    """Metadata for uploaded files."""
    filename: str
    file_hash: str
    size: int
    mime_type: str
    upload_timestamp: datetime

class SecurityManager:
    """Handles encryption and secure operations."""
    
    def __init__(self, encryption_key: str):
        """
        Initialize security manager with encryption key.
        
        Args:
            encryption_key (str): Base encryption key for securing data
        """
        if not encryption_key:
            raise ValueError("Encryption key cannot be empty")
            
        # Derive a proper length key using SHA-256
        key_bytes = hashlib.sha256(encryption_key.encode()).digest()
        # Convert to URL-safe base64-encoded bytes for Fernet
        self.key = base64.urlsafe_b64encode(key_bytes)
        self.fernet = Fernet(self.key)
        
    def encrypt_data(self, data: Any) -> bytes:
        """
        Encrypt data using Fernet symmetric encryption.
        
        Args:
            data: Data to encrypt (will be JSON serialized)
            
        Returns:
            bytes: Encrypted data
        """
        try:
            json_data = json.dumps(data)
            return self.fernet.encrypt(json_data.encode())
        except Exception as e:
            logging.error(f"Encryption failed: {str(e)}")
            raise RuntimeError(f"Failed to encrypt data: {str(e)}")
            
    def decrypt_data(self, encrypted_data: bytes) -> Any:
        """
        Decrypt data using Fernet symmetric encryption.
        
        Args:
            encrypted_data (bytes): Data to decrypt
            
        Returns:
            Any: Decrypted and JSON-parsed data
        """
        try:
            decrypted_data = self.fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logging.error(f"Decryption failed: {str(e)}")
            raise RuntimeError(f"Failed to decrypt data: {str(e)}")
            
    def secure_hash(self, data: bytes) -> str:
        """
        Generate a secure hash of data using SHA-256.
        
        Args:
            data (bytes): Data to hash
            
        Returns:
            str: Hexadecimal hash string
        """
        return hashlib.sha256(data).hexdigest()
class SessionManager:
    def __init__(self, expiry_time: int = 3600, temp_dir: str = "temp"):
        """Initialize session manager."""
        self.expiry_time = expiry_time
        self.temp_dir = Path(temp_dir)
        self.sessions: dict = {}
        
        # Ensure temp directory exists
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
    def create_session(self, session_id: str = None) -> str:
        """Create or validate a session and return session ID."""
        if session_id and session_id in self.sessions:
            return session_id
            
        # Use provided session_id or generate new one
        new_session_id = session_id or str(int(time.time()))
        self.sessions[new_session_id] = {
            'created_at': datetime.now(),
            'last_accessed': datetime.now(),
            'files': [],
            'temp_dir': self.temp_dir / new_session_id
        }
        
        # Create session directory
        self.sessions[new_session_id]['temp_dir'].mkdir(exist_ok=True)
        return new_session_id
        
    def validate_session(self, session_id: str) -> bool:
        """Validate session and update last accessed time."""
        if session_id not in self.sessions:
            return False
            
        session = self.sessions[session_id]
        now = datetime.now()
        
        # Check if session has expired
        if now - session['last_accessed'] > timedelta(seconds=self.expiry_time):
            self.cleanup_session(session_id)
            return False
            
        # Update last accessed time
        session['last_accessed'] = now
        return True
        
    def add_file_to_session(self, session_id: str, filename: str, file_hash: str, size: int) -> None:
        """Add file metadata to session."""
        # Create session if it doesn't exist
        if session_id not in self.sessions:
            self.create_session(session_id)
            
        if session_id not in self.sessions:
            raise ValueError("Invalid session ID")
            
        file_meta = FileMetadata(
            filename=filename,
            file_hash=file_hash,
            size=size,
            mime_type=mimetypes.guess_type(filename)[0] or 'application/octet-stream',
            upload_timestamp=datetime.now()
        )
        
        self.sessions[session_id]['files'].append(file_meta)
            
    def cleanup_session(self, session_id: str) -> None:
        """
        Clean up session and remove associated files.
        
        Args:
            session_id (str): Session ID to clean up
        """
        if session_id not in self.sessions:
            return
            
        session = self.sessions[session_id]
        session_dir = session['temp_dir']
        
        # Remove all files in session directory
        try:
            for file_path in session_dir.glob('*'):
                try:
                    file_path.unlink()
                except Exception as e:
                    logging.error(f"Error removing file {file_path}: {str(e)}")
                    
            # Remove session directory
            session_dir.rmdir()
        except Exception as e:
            logging.error(f"Error cleaning up session directory: {str(e)}")
            
        # Remove session from dictionary
        del self.sessions[session_id]
        
    def cleanup_expired_sessions(self) -> None:
        """Clean up all expired sessions."""
        now = datetime.now()
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if now - session['last_accessed'] > timedelta(seconds=self.expiry_time)
        ]
        
        for session_id in expired_sessions:
            self.cleanup_session(session_id)

class SecureFileHandler:
    """Handles secure file operations."""
    
    def __init__(self, 
                 security_manager: SecurityManager,
                 allowed_extensions: List[str] = None,
                 max_file_size: int = 100 * 1024 * 1024):  # 100MB default
        """
        Initialize secure file handler.
        
        Args:
            security_manager (SecurityManager): Security manager instance
            allowed_extensions (List[str]): List of allowed file extensions
            max_file_size (int): Maximum file size in bytes
        """
        self.security_manager = security_manager
        self.allowed_extensions = allowed_extensions or ['.pdf']
        self.max_file_size = max_file_size
        
    def validate_file(self, file_content: bytes, filename: str) -> None:
        """
        Validate file content and name.
        
        Args:
            file_content (bytes): File content
            filename (str): Original filename
            
        Raises:
            ValueError: If file validation fails
        """
        # Check file size
        if len(file_content) > self.max_file_size:
            raise ValueError(f"File size exceeds maximum limit of {self.max_file_size} bytes")
            
        # Check file extension
        ext = Path(filename).suffix.lower()
        if ext not in self.allowed_extensions:
            raise ValueError(f"File type {ext} not allowed. Allowed types: {self.allowed_extensions}")
            
        # Basic content validation for PDFs
        if ext == '.pdf' and not file_content.startswith(b'%PDF-'):
            raise ValueError("Invalid PDF file format")
            
    def save_file_securely(self, 
                          file_content: bytes, 
                          filename: str, 
                          session_dir: Path) -> Path:
        """
        Save file securely with encryption.
        
        Args:
            file_content (bytes): File content
            filename (str): Original filename
            session_dir (Path): Session directory path
            
        Returns:
            Path: Path to saved file
        """
        # Generate secure filename
        secure_filename = self.security_manager.secure_hash(file_content)[:16]
        ext = Path(filename).suffix.lower()
        secure_path = session_dir / f"{secure_filename}{ext}"
        
        # Encrypt and save file
        encrypted_content = self.security_manager.encrypt_data(file_content)
        secure_path.write_bytes(encrypted_content)
        
        return secure_path
        
    def read_file_securely(self, file_path: Path) -> bytes:
        """
        Read and decrypt file content.
        
        Args:
            file_path (Path): Path to encrypted file
            
        Returns:
            bytes: Decrypted file content
        """
        encrypted_content = file_path.read_bytes()
        return self.security_manager.decrypt_data(encrypted_content)