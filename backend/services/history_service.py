"""
History Service for tracking loan applications and sanction letters
Provides persistence and retrieval of application history
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from models.history import (
    LoanApplicationHistory, SanctionLetterHistory, ApplicationStatus
)

logger = logging.getLogger(__name__)


class HistoryService:
    """Service for managing loan application and sanction letter history"""
    
    def __init__(self, storage_path: str = "data/history"):
        self.storage_path = Path(storage_path)
        self.applications_file = self.storage_path / "applications.json"
        self.sanction_letters_file = self.storage_path / "sanction_letters.json"
        self._ensure_storage()
        
    def _ensure_storage(self):
        """Create storage directory and files if they don't exist"""
        self.storage_path.mkdir(parents=True, exist_ok=True)
        if not self.applications_file.exists():
            self._save_json(self.applications_file, [])
        if not self.sanction_letters_file.exists():
            self._save_json(self.sanction_letters_file, [])
    
    def _load_json(self, filepath: Path) -> List[Dict]:
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _save_json(self, filepath: Path, data: List[Dict]):
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    # Application History Methods
    def create_application(self, **kwargs) -> LoanApplicationHistory:
        """Create a new loan application record"""
        app_id = f"APP_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8].upper()}"
        
        # Convert status string to enum if needed
        if 'status' in kwargs and isinstance(kwargs['status'], str):
            try:
                kwargs['status'] = ApplicationStatus(kwargs['status'])
            except ValueError:
                kwargs['status'] = ApplicationStatus.INITIATED
        
        try:
            application = LoanApplicationHistory(id=app_id, **kwargs)
        except Exception as e:
            logger.error(f"Error creating application: {e}, kwargs: {kwargs}")
            raise
        
        applications = self._load_json(self.applications_file)
        applications.append(application.to_dict())
        self._save_json(self.applications_file, applications)
        
        logger.info(f"Created application: {app_id}")
        return application
    
    def update_application(self, app_id: str, **kwargs) -> Optional[LoanApplicationHistory]:
        """Update an existing application"""
        applications = self._load_json(self.applications_file)
        
        for i, app in enumerate(applications):
            if app['id'] == app_id:
                app.update(kwargs)
                app['updated_at'] = datetime.now().isoformat()
                applications[i] = app
                self._save_json(self.applications_file, applications)
                logger.info(f"Updated application: {app_id}")
                return LoanApplicationHistory.from_dict(app)
        return None
    
    def get_application(self, app_id: str) -> Optional[LoanApplicationHistory]:
        """Get application by ID"""
        applications = self._load_json(self.applications_file)
        for app in applications:
            if app['id'] == app_id:
                return LoanApplicationHistory.from_dict(app)
        return None
    
    def get_all_applications(self, limit: int = 50, status: Optional[str] = None) -> List[LoanApplicationHistory]:
        """Get all applications with optional filtering"""
        applications = self._load_json(self.applications_file)
        
        if status:
            applications = [a for a in applications if a.get('status') == status]
        
        # Sort by created_at descending
        applications.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return [LoanApplicationHistory.from_dict(a) for a in applications[:limit]]

    def get_applications_by_session(self, session_id: str) -> List[LoanApplicationHistory]:
        """Get applications for a specific session"""
        applications = self._load_json(self.applications_file)
        filtered = [a for a in applications if a.get('session_id') == session_id]
        return [LoanApplicationHistory.from_dict(a) for a in filtered]
    
    # Sanction Letter History Methods
    def create_sanction_letter_record(self, **kwargs) -> SanctionLetterHistory:
        """Create a sanction letter history record"""
        letter_id = kwargs.get('id') or f"SL_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8].upper()}"
        kwargs['id'] = letter_id
        
        letter = SanctionLetterHistory(**kwargs)
        
        letters = self._load_json(self.sanction_letters_file)
        letters.append(letter.to_dict())
        self._save_json(self.sanction_letters_file, letters)
        
        logger.info(f"Created sanction letter record: {letter_id}")
        return letter
    
    def get_sanction_letter(self, letter_id: str) -> Optional[SanctionLetterHistory]:
        """Get sanction letter by ID"""
        letters = self._load_json(self.sanction_letters_file)
        for letter in letters:
            if letter['id'] == letter_id:
                return SanctionLetterHistory.from_dict(letter)
        return None
    
    def get_all_sanction_letters(self, limit: int = 50) -> List[SanctionLetterHistory]:
        """Get all sanction letters"""
        letters = self._load_json(self.sanction_letters_file)
        letters.sort(key=lambda x: x.get('generated_at', ''), reverse=True)
        return [SanctionLetterHistory.from_dict(l) for l in letters[:limit]]
    
    def increment_download_count(self, letter_id: str) -> bool:
        """Increment download count for a sanction letter"""
        letters = self._load_json(self.sanction_letters_file)
        for i, letter in enumerate(letters):
            if letter['id'] == letter_id:
                letter['downloaded_count'] = letter.get('downloaded_count', 0) + 1
                letter['last_downloaded_at'] = datetime.now().isoformat()
                letters[i] = letter
                self._save_json(self.sanction_letters_file, letters)
                return True
        return False

    # Statistics Methods
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics"""
        applications = self._load_json(self.applications_file)
        letters = self._load_json(self.sanction_letters_file)
        
        total_apps = len(applications)
        approved = len([a for a in applications if a.get('status') == 'approved'])
        rejected = len([a for a in applications if a.get('status') == 'rejected'])
        pending = len([a for a in applications if a.get('status') in ['initiated', 'in_progress', 'verification_pending', 'underwriting']])
        
        total_sanctioned = sum(a.get('approved_amount', 0) or 0 for a in applications if a.get('status') == 'approved')
        
        return {
            'total_applications': total_apps,
            'approved': approved,
            'rejected': rejected,
            'pending': pending,
            'approval_rate': round((approved / total_apps * 100), 1) if total_apps > 0 else 0,
            'total_sanctioned_amount': total_sanctioned,
            'total_sanction_letters': len(letters),
            'total_downloads': sum(l.get('downloaded_count', 0) for l in letters)
        }


# Global instance
_history_service: Optional[HistoryService] = None

def get_history_service() -> HistoryService:
    """Get or create the history service singleton"""
    global _history_service
    if _history_service is None:
        _history_service = HistoryService()
    return _history_service
