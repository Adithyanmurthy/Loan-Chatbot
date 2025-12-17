"""
Loan Application History Models
Tracks all loan applications, approvals, rejections, and sanction letters
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class ApplicationStatus(str, Enum):
    """Enumeration for application status"""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    VERIFICATION_PENDING = "verification_pending"
    UNDERWRITING = "underwriting"
    APPROVED = "approved"
    REJECTED = "rejected"
    DOCUMENTS_REQUIRED = "documents_required"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class LoanApplicationHistory(BaseModel):
    """Model for tracking loan application history"""
    id: str = Field(..., description="Unique application ID")
    session_id: str = Field(..., description="Session ID")
    customer_name: str = Field(..., description="Customer name")
    customer_phone: Optional[str] = Field(None, description="Customer phone")
    customer_email: Optional[str] = Field(None, description="Customer email")
    customer_city: Optional[str] = Field(None, description="Customer city")
    requested_amount: float = Field(..., gt=0, description="Requested loan amount")
    approved_amount: Optional[float] = Field(None, description="Approved amount")
    tenure: int = Field(..., ge=6, le=360, description="Loan tenure in months")
    interest_rate: float = Field(..., ge=0, le=50, description="Interest rate")
    emi: Optional[float] = Field(None, description="Monthly EMI")
    status: ApplicationStatus = Field(default=ApplicationStatus.INITIATED)
    credit_score: Optional[int] = Field(None, ge=300, le=900)
    verification_status: Optional[str] = Field(None, description="KYC verification status")
    sanction_letter_id: Optional[str] = Field(None, description="Sanction letter ID if approved")
    sanction_letter_url: Optional[str] = Field(None, description="Download URL")
    rejection_reason: Optional[str] = Field(None, description="Reason if rejected")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = Field(None)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    def to_dict(self) -> dict:
        data = self.dict()
        # Convert enum to string for JSON serialization
        if 'status' in data and hasattr(data['status'], 'value'):
            data['status'] = data['status'].value
        # Convert datetime objects to ISO format strings
        for key in ['created_at', 'updated_at', 'completed_at']:
            if key in data and data[key] is not None:
                if hasattr(data[key], 'isoformat'):
                    data[key] = data[key].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'LoanApplicationHistory':
        # Convert status string to enum if needed
        if 'status' in data and isinstance(data['status'], str):
            try:
                data['status'] = ApplicationStatus(data['status'])
            except ValueError:
                data['status'] = ApplicationStatus.INITIATED
        return cls(**data)


class SanctionLetterHistory(BaseModel):
    """Model for tracking generated sanction letters"""
    id: str = Field(..., description="Unique letter ID")
    application_id: str = Field(..., description="Associated application ID")
    customer_name: str = Field(..., description="Customer name")
    loan_amount: float = Field(..., gt=0, description="Sanctioned amount")
    tenure: int = Field(..., description="Loan tenure")
    interest_rate: float = Field(..., description="Interest rate")
    emi: float = Field(..., description="Monthly EMI")
    filename: str = Field(..., description="PDF filename")
    download_url: str = Field(..., description="Download URL")
    file_path: Optional[str] = Field(None, description="Server file path")
    generated_at: datetime = Field(default_factory=datetime.now)
    downloaded_count: int = Field(default=0, description="Download count")
    last_downloaded_at: Optional[datetime] = Field(None)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    def to_dict(self) -> dict:
        return self.dict()

    @classmethod
    def from_dict(cls, data: dict) -> 'SanctionLetterHistory':
        return cls(**data)
