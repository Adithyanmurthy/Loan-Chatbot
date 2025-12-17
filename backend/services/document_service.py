"""
Document handling service for file uploads and processing
Based on requirements: 7.1, 7.2
"""

import os
import uuid
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from datetime import datetime
import json
import logging

from models.documents import FileUpload, DocumentType, FileUploadStatus, DocumentProcessingResult

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for handling document uploads and storage"""
    
    def __init__(self, upload_folder: str = "uploads", max_file_size: int = 10 * 1024 * 1024):
        """
        Initialize document service
        
        Args:
            upload_folder: Directory to store uploaded files
            max_file_size: Maximum file size in bytes (default 10MB)
        """
        self.upload_folder = upload_folder
        self.max_file_size = max_file_size
        self.allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png'}
        self.allowed_mime_types = {
            'application/pdf',
            'image/jpeg', 
            'image/jpg',
            'image/png'
        }
        
        # Create upload directory if it doesn't exist
        os.makedirs(upload_folder, exist_ok=True)
        
        # Create subdirectories for different document types
        for doc_type in DocumentType:
            type_dir = os.path.join(upload_folder, doc_type.value)
            os.makedirs(type_dir, exist_ok=True)
    
    def validate_file(self, file: FileStorage) -> Tuple[bool, Optional[str]]:
        """
        Validate uploaded file against security and format requirements
        
        Args:
            file: Uploaded file object
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file:
            return False, "No file provided"
        
        if not file.filename:
            return False, "No filename provided"
        
        # Check file size
        if hasattr(file, 'content_length') and file.content_length:
            if file.content_length > self.max_file_size:
                return False, f"File size exceeds maximum limit of {self.max_file_size / (1024*1024):.1f}MB"
        
        # Check file extension
        filename = file.filename.lower()
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in self.allowed_extensions:
            return False, f"File type not allowed. Supported formats: {', '.join(self.allowed_extensions)}"
        
        # Check MIME type if available
        if file.mimetype and file.mimetype not in self.allowed_mime_types:
            return False, f"Invalid file type. Expected: {', '.join(self.allowed_mime_types)}"
        
        # Check for dangerous filename patterns
        secure_name = secure_filename(file.filename)
        if not secure_name or secure_name != file.filename:
            return False, "Filename contains invalid characters"
        
        return True, None
    
    def generate_unique_filename(self, original_filename: str, document_type: DocumentType) -> str:
        """
        Generate a unique filename to prevent conflicts
        
        Args:
            original_filename: Original uploaded filename
            document_type: Type of document being uploaded
            
        Returns:
            Unique filename with timestamp and UUID
        """
        # Get file extension
        _, ext = os.path.splitext(original_filename)
        
        # Generate unique identifier
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        # Create secure filename
        base_name = secure_filename(os.path.splitext(original_filename)[0])
        if not base_name:
            base_name = "document"
        
        return f"{document_type.value}_{timestamp}_{unique_id}_{base_name}{ext}"
    
    def save_file(self, file: FileStorage, document_type: DocumentType) -> FileUpload:
        """
        Save uploaded file to disk and create FileUpload record
        
        Args:
            file: Uploaded file object
            document_type: Type of document
            
        Returns:
            FileUpload model instance
            
        Raises:
            ValueError: If file validation fails
            IOError: If file save operation fails
        """
        # Validate file first
        is_valid, error_msg = self.validate_file(file)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Generate unique filename and upload ID
        upload_id = str(uuid.uuid4())
        unique_filename = self.generate_unique_filename(file.filename, document_type)
        
        # Determine file path
        type_dir = os.path.join(self.upload_folder, document_type.value)
        file_path = os.path.join(type_dir, unique_filename)
        
        try:
            # Create FileUpload record
            file_upload = FileUpload(
                id=upload_id,
                filename=file.filename,
                file_type=file.mimetype or 'application/octet-stream',
                file_size=0,  # Will be updated after save
                document_type=document_type
            )
            
            # Mark upload as starting
            file_upload.start_upload()
            
            # Save file to disk
            file.save(file_path)
            
            # Get actual file size
            file_size = os.path.getsize(file_path)
            file_upload.file_size = file_size
            
            # Validate file size after save
            if file_size > self.max_file_size:
                os.remove(file_path)  # Clean up
                raise ValueError(f"File size {file_size} exceeds maximum limit of {self.max_file_size}")
            
            # Mark upload as completed
            file_upload.mark_completed()
            
            # Store file path for retrieval
            file_upload.extracted_data = {"file_path": file_path}
            
            logger.info(f"File uploaded successfully: {upload_id} -> {file_path}")
            return file_upload
            
        except Exception as e:
            # Clean up file if it was partially saved
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            
            # Mark upload as failed
            if 'file_upload' in locals():
                file_upload.mark_failed(str(e))
                return file_upload
            else:
                raise IOError(f"Failed to save file: {str(e)}")
    
    def get_file_path(self, upload_id: str) -> Optional[str]:
        """
        Get file path for a given upload ID
        
        Args:
            upload_id: Upload identifier
            
        Returns:
            File path if found, None otherwise
        """
        # This would typically query a database
        # For now, we'll implement a simple file-based storage
        metadata_file = os.path.join(self.upload_folder, f"{upload_id}.json")
        
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    return metadata.get('file_path')
            except Exception as e:
                logger.error(f"Error reading metadata for {upload_id}: {e}")
        
        return None
    
    def save_upload_metadata(self, file_upload: FileUpload) -> None:
        """
        Save upload metadata to disk for retrieval
        
        Args:
            file_upload: FileUpload instance to save
        """
        metadata_file = os.path.join(self.upload_folder, f"{file_upload.id}.json")
        
        try:
            with open(metadata_file, 'w') as f:
                json.dump(file_upload.to_dict(), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving metadata for {file_upload.id}: {e}")
    
    def load_upload_metadata(self, upload_id: str) -> Optional[FileUpload]:
        """
        Load upload metadata from disk
        
        Args:
            upload_id: Upload identifier
            
        Returns:
            FileUpload instance if found, None otherwise
        """
        metadata_file = os.path.join(self.upload_folder, f"{upload_id}.json")
        
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                    return FileUpload.from_dict(data)
            except Exception as e:
                logger.error(f"Error loading metadata for {upload_id}: {e}")
        
        return None
    
    def delete_file(self, upload_id: str) -> bool:
        """
        Delete uploaded file and its metadata
        
        Args:
            upload_id: Upload identifier
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            # Load metadata to get file path
            file_upload = self.load_upload_metadata(upload_id)
            if not file_upload:
                return False
            
            # Delete actual file
            if file_upload.extracted_data and 'file_path' in file_upload.extracted_data:
                file_path = file_upload.extracted_data['file_path']
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            # Delete metadata file
            metadata_file = os.path.join(self.upload_folder, f"{upload_id}.json")
            if os.path.exists(metadata_file):
                os.remove(metadata_file)
            
            logger.info(f"File deleted successfully: {upload_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file {upload_id}: {e}")
            return False
    
    def list_uploads(self, document_type: Optional[DocumentType] = None) -> List[FileUpload]:
        """
        List all uploads, optionally filtered by document type
        
        Args:
            document_type: Optional filter by document type
            
        Returns:
            List of FileUpload instances
        """
        uploads = []
        
        try:
            # Find all metadata files
            for filename in os.listdir(self.upload_folder):
                if filename.endswith('.json'):
                    upload_id = filename[:-5]  # Remove .json extension
                    file_upload = self.load_upload_metadata(upload_id)
                    
                    if file_upload:
                        if document_type is None or file_upload.document_type == document_type:
                            uploads.append(file_upload)
        
        except Exception as e:
            logger.error(f"Error listing uploads: {e}")
        
        return uploads
    
    def calculate_file_hash(self, file_path: str) -> Optional[str]:
        """
        Calculate SHA-256 hash of a file for integrity verification
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA-256 hash string or None if error
        """
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return None