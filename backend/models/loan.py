"""
Loan application and processing models
Based on requirements: 1.4, 2.1, 3.1, 4.1
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class LoanStatus(str, Enum):
    """Enumeration for loan application status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_DOCUMENTS = "requires_documents"


class LoanApplication(BaseModel):
    """Model for loan application"""
    id: str = Field(..., description="Unique application identifier")
    customer_id: str = Field(..., description="Customer identifier")
    requested_amount: float = Field(..., gt=0, description="Requested loan amount")
    tenure: int = Field(..., ge=6, le=360, description="Loan tenure in months")
    interest_rate: float = Field(..., ge=0, le=50, description="Interest rate percentage")
    emi: float = Field(..., ge=0, description="Calculated EMI amount")
    status: LoanStatus = Field(default=LoanStatus.PENDING, description="Application status")
    created_at: datetime = Field(default_factory=datetime.now, description="Application creation time")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection")

    @validator('requested_amount')
    def validate_amount(cls, v):
        """Validate loan amount"""
        if v <= 0:
            raise ValueError('Loan amount must be positive')
        if v > 10000000:  # 1 crore max
            raise ValueError('Loan amount cannot exceed ₹1 crore')
        return v

    @validator('tenure')
    def validate_tenure(cls, v):
        """Validate loan tenure"""
        if v < 6:
            raise ValueError('Minimum tenure is 6 months')
        if v > 360:
            raise ValueError('Maximum tenure is 360 months (30 years)')
        return v

    @validator('interest_rate')
    def validate_interest_rate(cls, v):
        """Validate interest rate"""
        if v < 0:
            raise ValueError('Interest rate cannot be negative')
        if v > 50:
            raise ValueError('Interest rate cannot exceed 50%')
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def calculate_emi(self) -> float:
        """Calculate EMI using standard formula"""
        principal = self.requested_amount
        monthly_rate = self.interest_rate / (12 * 100)
        
        if monthly_rate == 0:
            return principal / self.tenure
        
        emi = principal * monthly_rate * (1 + monthly_rate) ** self.tenure / ((1 + monthly_rate) ** self.tenure - 1)
        return round(emi, 2)

    def update_emi(self):
        """Update EMI based on current amount, rate, and tenure"""
        self.emi = self.calculate_emi()

    def approve(self, approval_timestamp: Optional[datetime] = None):
        """Mark application as approved"""
        self.status = LoanStatus.APPROVED
        self.approved_at = approval_timestamp or datetime.now()
        self.rejection_reason = None

    def reject(self, reason: str):
        """Mark application as rejected with reason"""
        self.status = LoanStatus.REJECTED
        self.rejection_reason = reason
        self.approved_at = None

    def require_documents(self):
        """Mark application as requiring additional documents"""
        self.status = LoanStatus.REQUIRES_DOCUMENTS

    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return self.dict()

    @classmethod
    def from_dict(cls, data: dict) -> 'LoanApplication':
        """Create model from dictionary"""
        return cls(**data)


class UnderwritingDecision(BaseModel):
    """Model for underwriting decision details"""
    application_id: str = Field(..., description="Loan application ID")
    decision: LoanStatus = Field(..., description="Underwriting decision")
    credit_score: int = Field(..., ge=300, le=900, description="Customer credit score")
    pre_approved_limit: float = Field(..., ge=0, description="Pre-approved limit")
    debt_to_income_ratio: Optional[float] = Field(None, description="Debt-to-income ratio")
    decision_factors: Dict[str, Any] = Field(default_factory=dict, description="Factors influencing decision")
    created_at: datetime = Field(default_factory=datetime.now, description="Decision timestamp")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def add_decision_factor(self, factor: str, value: Any, weight: float = 1.0):
        """Add a factor that influenced the underwriting decision"""
        self.decision_factors[factor] = {
            'value': value,
            'weight': weight,
            'timestamp': datetime.now().isoformat()
        }

    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return self.dict()

    @classmethod
    def from_dict(cls, data: dict) -> 'UnderwritingDecision':
        """Create model from dictionary"""
        return cls(**data)