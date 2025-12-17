"""
Customer-related data models
Based on requirements: 1.4, 2.1, 3.1, 4.1
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator
import re


class LoanDetails(BaseModel):
    """Model for existing loan details"""
    id: str = Field(..., description="Unique loan identifier")
    amount: float = Field(..., gt=0, description="Loan amount")
    tenure: int = Field(..., gt=0, le=360, description="Loan tenure in months")
    interest_rate: float = Field(..., ge=0, le=50, description="Interest rate percentage")
    emi: float = Field(..., ge=0, description="Monthly EMI amount")
    status: str = Field(..., description="Current loan status")
    start_date: datetime = Field(..., description="Loan start date")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CustomerProfile(BaseModel):
    """Model for customer profile information"""
    id: str = Field(..., description="Unique customer identifier")
    name: str = Field(..., min_length=1, description="Customer full name")
    age: int = Field(..., ge=18, le=100, description="Customer age")
    city: str = Field(..., min_length=1, description="Customer city")
    phone: str = Field(..., description="Customer phone number")
    address: str = Field(..., min_length=1, description="Customer address")
    current_loans: List[LoanDetails] = Field(default_factory=list, description="List of current loans")
    credit_score: int = Field(..., ge=300, le=900, description="Credit score")
    pre_approved_limit: float = Field(..., ge=0, description="Pre-approved loan limit")
    salary: Optional[float] = Field(None, ge=0, description="Monthly salary")
    employment_type: str = Field(..., min_length=1, description="Type of employment")

    @validator('phone')
    def validate_phone(cls, v):
        """Validate Indian phone number format"""
        # Remove spaces and check format
        phone_clean = re.sub(r'\s+', '', v)
        if not re.match(r'^(\+91)?[6-9]\d{9}$', phone_clean):
            raise ValueError('Invalid Indian phone number format')
        return phone_clean

    @validator('name')
    def validate_name(cls, v):
        """Validate customer name"""
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

    @validator('city')
    def validate_city(cls, v):
        """Validate city name"""
        if not v.strip():
            raise ValueError('City cannot be empty')
        return v.strip()

    @validator('address')
    def validate_address(cls, v):
        """Validate address"""
        if not v.strip():
            raise ValueError('Address cannot be empty')
        return v.strip()

    @validator('employment_type')
    def validate_employment_type(cls, v):
        """Validate employment type"""
        valid_types = ['salaried', 'self_employed', 'business', 'professional', 'retired']
        if v.lower() not in valid_types:
            raise ValueError(f'Employment type must be one of: {", ".join(valid_types)}')
        return v.lower()

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return self.dict()

    @classmethod
    def from_dict(cls, data: dict) -> 'CustomerProfile':
        """Create model from dictionary"""
        return cls(**data)

    def calculate_debt_to_income_ratio(self) -> Optional[float]:
        """Calculate debt-to-income ratio if salary is available"""
        if not self.salary:
            return None
        
        total_emi = sum(loan.emi for loan in self.current_loans)
        return (total_emi / self.salary) * 100 if self.salary > 0 else 0

    def get_available_income(self) -> Optional[float]:
        """Calculate available income after existing EMIs"""
        if not self.salary:
            return None
        
        total_emi = sum(loan.emi for loan in self.current_loans)
        return max(0, self.salary - total_emi)

    def is_eligible_for_amount(self, requested_amount: float) -> bool:
        """Check basic eligibility for requested amount"""
        return (
            self.credit_score >= 700 and
            requested_amount <= self.pre_approved_limit * 2 and
            self.age >= 21
        )