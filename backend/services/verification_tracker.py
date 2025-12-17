"""
Verification Status Tracking and Reporting System
Manages verification status across customer sessions and provides reporting capabilities
Based on requirements: 3.5, 8.1
"""

import logging
import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import threading


class VerificationStatusType(str, Enum):
    """Enumeration for verification status types"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    FAILED = "failed"
    REQUIRES_DOCUMENTS = "requires_documents"
    EXPIRED = "expired"


class VerificationMethod(str, Enum):
    """Enumeration for verification methods"""
    AUTOMATIC_CRM = "automatic_crm"
    DOCUMENT_BASED = "document_based"
    MANUAL_REVIEW = "manual_review"
    HYBRID = "hybrid"


@dataclass
class VerificationRecord:
    """Data class for verification records"""
    customer_id: str
    session_id: str
    status: VerificationStatusType
    method: Optional[VerificationMethod] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    verification_score: Optional[int] = None
    issues: List[str] = None
    verified_fields: List[str] = None
    required_documents: List[str] = None
    attempts: int = 0
    last_attempt_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []
        if self.verified_fields is None:
            self.verified_fields = []
        if self.required_documents is None:
            self.required_documents = []
        if self.metadata is None:
            self.metadata = {}
        if self.started_at is None and self.status != VerificationStatusType.NOT_STARTED:
            self.started_at = datetime.now()
        if self.expires_at is None and self.status == VerificationStatusType.VERIFIED:
            # Verification expires after 30 days
            self.expires_at = datetime.now() + timedelta(days=30)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper datetime serialization"""
        data = asdict(self)
        
        # Convert datetime objects to ISO strings
        for field in ['started_at', 'completed_at', 'expires_at', 'last_attempt_at']:
            if data[field]:
                data[field] = data[field].isoformat()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VerificationRecord':
        """Create from dictionary with proper datetime parsing"""
        # Convert ISO strings back to datetime objects
        for field in ['started_at', 'completed_at', 'expires_at', 'last_attempt_at']:
            if data.get(field):
                data[field] = datetime.fromisoformat(data[field])
        
        return cls(**data)
    
    def is_expired(self) -> bool:
        """Check if verification has expired"""
        if self.status != VerificationStatusType.VERIFIED or not self.expires_at:
            return False
        return datetime.now() > self.expires_at
    
    def update_status(self, new_status: VerificationStatusType, **kwargs):
        """Update verification status with optional additional data"""
        self.status = new_status
        self.last_attempt_at = datetime.now()
        
        if new_status == VerificationStatusType.IN_PROGRESS and not self.started_at:
            self.started_at = datetime.now()
        elif new_status in [VerificationStatusType.VERIFIED, VerificationStatusType.FAILED]:
            self.completed_at = datetime.now()
            if new_status == VerificationStatusType.VERIFIED and not self.expires_at:
                self.expires_at = datetime.now() + timedelta(days=30)
        
        # Update additional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def add_attempt(self):
        """Increment attempt counter"""
        self.attempts += 1
        self.last_attempt_at = datetime.now()


class VerificationTracker:
    """
    Verification Status Tracking and Reporting System.
    Manages verification records across customer sessions with persistence.
    """
    
    def __init__(self, storage_path: str = "backend/data/verification_records.json"):
        """
        Initialize verification tracker.
        
        Args:
            storage_path: Path to store verification records
        """
        self.storage_path = storage_path
        self.records: Dict[str, VerificationRecord] = {}
        self._lock = threading.Lock()
        
        # Setup logging
        self.logger = logging.getLogger("verification_tracker")
        self.logger.setLevel(logging.INFO)
        
        # Ensure storage directory exists
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        
        # Load existing records
        self._load_records()
        
        self.logger.info(f"Verification Tracker initialized with {len(self.records)} existing records")
    
    def start_verification(self, customer_id: str, session_id: str, 
                          method: VerificationMethod = VerificationMethod.AUTOMATIC_CRM) -> VerificationRecord:
        """
        Start verification process for a customer.
        
        Args:
            customer_id: Customer identifier
            session_id: Session identifier
            method: Verification method to use
            
        Returns:
            VerificationRecord for the started verification
        """
        with self._lock:
            record_key = f"{customer_id}_{session_id}"
            
            # Check if verification already exists for this session
            if record_key in self.records:
                existing_record = self.records[record_key]
                if existing_record.status == VerificationStatusType.VERIFIED and not existing_record.is_expired():
                    self.logger.info(f"Using existing valid verification for customer {customer_id}")
                    return existing_record
            
            # Create new verification record
            record = VerificationRecord(
                customer_id=customer_id,
                session_id=session_id,
                status=VerificationStatusType.IN_PROGRESS,
                method=method,
                started_at=datetime.now()
            )
            
            self.records[record_key] = record
            self._save_records()
            
            self.logger.info(f"Started verification for customer {customer_id} using method {method.value}")
            return record
    
    def update_verification(self, customer_id: str, session_id: str, 
                           status: VerificationStatusType, **kwargs) -> Optional[VerificationRecord]:
        """
        Update verification status and details.
        
        Args:
            customer_id: Customer identifier
            session_id: Session identifier
            status: New verification status
            **kwargs: Additional fields to update
            
        Returns:
            Updated VerificationRecord or None if not found
        """
        with self._lock:
            record_key = f"{customer_id}_{session_id}"
            
            if record_key not in self.records:
                self.logger.warning(f"No verification record found for customer {customer_id}, session {session_id}")
                return None
            
            record = self.records[record_key]
            record.update_status(status, **kwargs)
            
            self._save_records()
            
            self.logger.info(f"Updated verification for customer {customer_id} to status {status.value}")
            return record
    
    def get_verification_status(self, customer_id: str, session_id: str) -> Optional[VerificationRecord]:
        """
        Get current verification status for a customer session.
        
        Args:
            customer_id: Customer identifier
            session_id: Session identifier
            
        Returns:
            VerificationRecord or None if not found
        """
        record_key = f"{customer_id}_{session_id}"
        record = self.records.get(record_key)
        
        if record and record.is_expired():
            # Mark as expired
            with self._lock:
                record.status = VerificationStatusType.EXPIRED
                self._save_records()
        
        return record
    
    def get_customer_verification_history(self, customer_id: str) -> List[VerificationRecord]:
        """
        Get verification history for a customer across all sessions.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            List of VerificationRecord objects
        """
        return [record for record in self.records.values() 
                if record.customer_id == customer_id]
    
    def is_customer_verified(self, customer_id: str) -> bool:
        """
        Check if customer has any valid (non-expired) verification.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            True if customer has valid verification
        """
        customer_records = self.get_customer_verification_history(customer_id)
        
        for record in customer_records:
            if record.status == VerificationStatusType.VERIFIED and not record.is_expired():
                return True
        
        return False
    
    def get_latest_verification(self, customer_id: str) -> Optional[VerificationRecord]:
        """
        Get the most recent verification record for a customer.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            Most recent VerificationRecord or None
        """
        customer_records = self.get_customer_verification_history(customer_id)
        
        if not customer_records:
            return None
        
        # Sort by started_at timestamp, most recent first
        sorted_records = sorted(customer_records, 
                               key=lambda r: r.started_at or datetime.min, 
                               reverse=True)
        
        return sorted_records[0]
    
    def add_verification_attempt(self, customer_id: str, session_id: str, 
                                issues: List[str] = None) -> Optional[VerificationRecord]:
        """
        Record a verification attempt with optional issues.
        
        Args:
            customer_id: Customer identifier
            session_id: Session identifier
            issues: List of issues encountered during attempt
            
        Returns:
            Updated VerificationRecord or None if not found
        """
        with self._lock:
            record_key = f"{customer_id}_{session_id}"
            
            if record_key not in self.records:
                return None
            
            record = self.records[record_key]
            record.add_attempt()
            
            if issues:
                record.issues.extend(issues)
                # Remove duplicates while preserving order
                record.issues = list(dict.fromkeys(record.issues))
            
            self._save_records()
            
            self.logger.info(f"Recorded verification attempt #{record.attempts} for customer {customer_id}")
            return record
    
    def get_verification_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get verification statistics for the specified period.
        
        Args:
            days: Number of days to include in statistics
            
        Returns:
            Dictionary containing verification statistics
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_records = [record for record in self.records.values() 
                         if record.started_at and record.started_at > cutoff_date]
        
        if not recent_records:
            return {
                "total_verifications": 0,
                "success_rate": 0,
                "average_attempts": 0,
                "method_distribution": {},
                "status_distribution": {},
                "period_days": days
            }
        
        # Calculate statistics
        total_verifications = len(recent_records)
        successful_verifications = sum(1 for r in recent_records 
                                     if r.status == VerificationStatusType.VERIFIED)
        success_rate = (successful_verifications / total_verifications) * 100
        
        total_attempts = sum(r.attempts for r in recent_records)
        average_attempts = total_attempts / total_verifications if total_verifications > 0 else 0
        
        # Method distribution
        method_counts = {}
        for record in recent_records:
            method = record.method.value if record.method else "unknown"
            method_counts[method] = method_counts.get(method, 0) + 1
        
        # Status distribution
        status_counts = {}
        for record in recent_records:
            status = record.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_verifications": total_verifications,
            "successful_verifications": successful_verifications,
            "success_rate": round(success_rate, 2),
            "average_attempts": round(average_attempts, 2),
            "method_distribution": method_counts,
            "status_distribution": status_counts,
            "period_days": days
        }
    
    def cleanup_expired_records(self) -> int:
        """
        Remove expired verification records.
        
        Returns:
            Number of records cleaned up
        """
        with self._lock:
            initial_count = len(self.records)
            
            # Keep records that are not expired or are recent (within 90 days)
            cutoff_date = datetime.now() - timedelta(days=90)
            
            self.records = {
                key: record for key, record in self.records.items()
                if (record.status != VerificationStatusType.EXPIRED and
                    (record.started_at is None or record.started_at > cutoff_date))
            }
            
            cleaned_count = initial_count - len(self.records)
            
            if cleaned_count > 0:
                self._save_records()
                self.logger.info(f"Cleaned up {cleaned_count} expired verification records")
            
            return cleaned_count
    
    def _load_records(self):
        """Load verification records from storage"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    
                    for key, record_data in data.items():
                        try:
                            record = VerificationRecord.from_dict(record_data)
                            self.records[key] = record
                        except Exception as e:
                            self.logger.warning(f"Failed to load verification record {key}: {str(e)}")
                
                self.logger.info(f"Loaded {len(self.records)} verification records from storage")
        except Exception as e:
            self.logger.error(f"Failed to load verification records: {str(e)}")
            self.records = {}
    
    def _save_records(self):
        """Save verification records to storage"""
        try:
            data = {key: record.to_dict() for key, record in self.records.items()}
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save verification records: {str(e)}")
    
    def export_records(self, output_path: str, customer_id: str = None) -> bool:
        """
        Export verification records to a file.
        
        Args:
            output_path: Path to export file
            customer_id: Optional customer ID to filter records
            
        Returns:
            True if export successful
        """
        try:
            records_to_export = self.records
            
            if customer_id:
                records_to_export = {
                    key: record for key, record in self.records.items()
                    if record.customer_id == customer_id
                }
            
            data = {key: record.to_dict() for key, record in records_to_export.items()}
            
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Exported {len(data)} verification records to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export verification records: {str(e)}")
            return False


# Global verification tracker instance
_verification_tracker = None


def get_verification_tracker() -> VerificationTracker:
    """Get global verification tracker instance"""
    global _verification_tracker
    if _verification_tracker is None:
        _verification_tracker = VerificationTracker()
    return _verification_tracker