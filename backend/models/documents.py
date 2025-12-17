"""
Document and file handling models
Based on requirements: 1.4, 2.1, 3.1, 4.1
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class FileUploadStatus(str, Enum):
    """Enumeration for file upload status"""
    PENDING = "pending"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentType(str, Enum):
    """Enumeration for document types"""
    SALARY_SLIP = "salary_slip"
    BANK_STATEMENT = "bank_statement"
    ID_PROOF = "id_proof"
    ADDRESS_PROOF = "address_proof"
    OTHER = "other"


class FileUpload(BaseModel):
    """Model for file upload tracking"""
    id: str = Field(..., description="Unique upload identifier")
    filename: str = Field(..., min_length=1, description="Original filename")
    file_type: str = Field(..., description="MIME type of the file")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    upload_status: FileUploadStatus = Field(default=FileUploadStatus.PENDING, description="Upload status")
    uploaded_at: Optional[datetime] = Field(None, description="Upload completion timestamp")
    error: Optional[str] = Field(None, description="Error message if upload failed")
    document_type: DocumentType = Field(default=DocumentType.OTHER, description="Type of document")
    extracted_data: Optional[Dict[str, Any]] = Field(None, description="Data extracted from document")

    @validator('file_size')
    def validate_file_size(cls, v):
        """Validate file size (max 10MB)"""
        max_size = 10 * 1024 * 1024  # 10MB
        if v > max_size:
            raise ValueError(f'File size cannot exceed {max_size} bytes (10MB)')
        return v

    @validator('file_type')
    def validate_file_type(cls, v):
        """Validate file type for document uploads"""
        allowed_types = [
            'application/pdf',
            'image/jpeg',
            'image/jpg',
            'image/png'
        ]
        if v.lower() not in allowed_types:
            raise ValueError(f'File type must be one of: {", ".join(allowed_types)}')
        return v.lower()

    @validator('filename')
    def validate_filename(cls, v):
        """Validate filename"""
        if not v.strip():
            raise ValueError('Filename cannot be empty')
        # Check for potentially dangerous characters
        dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
        for char in dangerous_chars:
            if char in v:
                raise ValueError(f'Filename contains invalid character: {char}')
        return v.strip()

    def mark_completed(self, extracted_data: Optional[Dict[str, Any]] = None):
        """Mark upload as completed"""
        self.upload_status = FileUploadStatus.COMPLETED
        self.uploaded_at = datetime.now()
        self.error = None
        if extracted_data:
            self.extracted_data = extracted_data

    def mark_failed(self, error_message: str):
        """Mark upload as failed"""
        self.upload_status = FileUploadStatus.FAILED
        self.error = error_message

    def start_upload(self):
        """Mark upload as in progress"""
        self.upload_status = FileUploadStatus.UPLOADING

    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return self.dict()

    @classmethod
    def from_dict(cls, data: dict) -> 'FileUpload':
        """Create model from dictionary"""
        return cls(**data)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SanctionLetter(BaseModel):
    """Model for sanction letter generation and management"""
    id: str = Field(..., description="Unique sanction letter identifier")
    loan_application_id: str = Field(..., description="Associated loan application ID")
    filename: str = Field(..., description="Generated PDF filename")
    download_url: str = Field(..., description="URL for downloading the document")
    generated_at: datetime = Field(default_factory=datetime.now, description="Generation timestamp")
    expires_at: datetime = Field(..., description="Download link expiration")
    file_path: Optional[str] = Field(None, description="Server file path")
    file_size: Optional[int] = Field(None, description="Generated file size in bytes")

    @validator('expires_at', pre=True, always=True)
    def set_expiration(cls, v, values):
        """Set expiration time if not provided (default 30 days)"""
        if v is None:
            generated_at = values.get('generated_at', datetime.now())
            return generated_at + timedelta(days=30)
        return v

    @validator('download_url')
    def validate_download_url(cls, v):
        """Validate download URL format"""
        if not v.startswith(('http://', 'https://', '/')):
            raise ValueError('Invalid download URL format')
        return v

    def is_expired(self) -> bool:
        """Check if download link has expired"""
        return datetime.now() > self.expires_at

    def extend_expiration(self, days: int = 30):
        """Extend expiration date"""
        self.expires_at = datetime.now() + timedelta(days=days)

    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return self.dict()

    @classmethod
    def from_dict(cls, data: dict) -> 'SanctionLetter':
        """Create model from dictionary"""
        return cls(**data)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DocumentProcessingResult(BaseModel):
    """Model for document processing results"""
    upload_id: str = Field(..., description="File upload ID")
    processing_status: str = Field(..., description="Processing status")
    extracted_fields: Dict[str, Any] = Field(default_factory=dict, description="Extracted field values")
    confidence_scores: Dict[str, float] = Field(default_factory=dict, description="Confidence scores for extracted fields")
    processing_errors: List[str] = Field(default_factory=list, description="List of processing errors")
    processed_at: datetime = Field(default_factory=datetime.now, description="Processing completion time")

    @validator('processing_status')
    def validate_processing_status(cls, v):
        """Validate processing status"""
        valid_statuses = ['success', 'partial_success', 'failed']
        if v not in valid_statuses:
            raise ValueError(f'Processing status must be one of: {", ".join(valid_statuses)}')
        return v

    def add_extracted_field(self, field_name: str, value: Any, confidence: float = 1.0):
        """Add an extracted field with confidence score"""
        self.extracted_fields[field_name] = value
        self.confidence_scores[field_name] = confidence

    def add_processing_error(self, error_message: str):
        """Add a processing error"""
        self.processing_errors.append(error_message)

    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return self.dict()

    @classmethod
    def from_dict(cls, data: dict) -> 'DocumentProcessingResult':
        """Create model from dictionary"""
        return cls(**data)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }