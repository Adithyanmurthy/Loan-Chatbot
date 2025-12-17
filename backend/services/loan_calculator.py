"""
Loan Calculation and Validation Service
Implements EMI calculation functions, affordability assessment logic, and term adjustment algorithms
Based on requirements: 2.2, 2.3
"""

import math
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from models.customer import CustomerProfile
from models.loan import LoanApplication


@dataclass
class LoanTerms:
    """Data class for loan terms"""
    amount: float
    tenure: int  # in months
    interest_rate: float  # annual percentage
    emi: float
    total_payable: float
    total_interest: float
    processing_fee: float


@dataclass
class AffordabilityAssessment:
    """Data class for affordability assessment results"""
    is_affordable: bool
    emi_to_income_ratio: float
    debt_to_income_ratio: float
    available_income: float
    max_affordable_emi: float
    max_affordable_amount: float
    risk_level: str  # low, medium, high
    assessment_factors: Dict[str, Any]


class LoanCalculator:
    """
    Service class for loan calculations and validations.
    Provides EMI calculations, affordability assessments, and term adjustments.
    """
    
    def __init__(self):
        """Initialize loan calculator with standard parameters"""
        # Standard calculation parameters
        self.max_emi_ratio = 0.50  # Maximum 50% of income for EMI
        self.safe_emi_ratio = 0.40  # Safe 40% of income for EMI
        self.conservative_emi_ratio = 0.30  # Conservative 30% of income for EMI
        
        # Tenure limits
        self.min_tenure_months = 6
        self.max_tenure_months = 360  # 30 years
        
        # Amount limits
        self.min_loan_amount = 10000  # ₹10,000
        self.max_loan_amount = 10000000  # ₹1 crore
        
        # Interest rate bounds
        self.min_interest_rate = 8.0
        self.max_interest_rate = 25.0
        
        # Processing fee parameters
        self.processing_fee_rates = {
            'standard': 0.02,  # 2%
            'premium': 0.015,  # 1.5%
            'promotional': 0.01  # 1%
        }
        
        self.max_processing_fee = 50000  # ₹50,000 cap

    def calculate_emi(self, principal: float, annual_interest_rate: float, 
                     tenure_months: int) -> float:
        """
        Calculate EMI using the standard loan formula.
        
        Formula: EMI = P * r * (1+r)^n / ((1+r)^n - 1)
        Where: P = Principal, r = Monthly interest rate, n = Number of months
        
        Args:
            principal: Loan principal amount
            annual_interest_rate: Annual interest rate as percentage
            tenure_months: Loan tenure in months
            
        Returns:
            Monthly EMI amount
            
        Raises:
            ValueError: If input parameters are invalid
        """
        # Validate inputs
        self._validate_calculation_inputs(principal, annual_interest_rate, tenure_months)
        
        # Convert annual rate to monthly decimal rate
        monthly_rate = annual_interest_rate / (12 * 100)
        
        # Handle zero interest rate case
        if monthly_rate == 0:
            return principal / tenure_months
        
        # Calculate EMI using standard formula
        numerator = principal * monthly_rate * (1 + monthly_rate) ** tenure_months
        denominator = (1 + monthly_rate) ** tenure_months - 1
        
        emi = numerator / denominator
        
        return round(emi, 2)

    def calculate_loan_terms(self, principal: float, annual_interest_rate: float, 
                           tenure_months: int, processing_fee_type: str = 'standard') -> LoanTerms:
        """
        Calculate comprehensive loan terms including EMI, total payable, and fees.
        
        Args:
            principal: Loan principal amount
            annual_interest_rate: Annual interest rate as percentage
            tenure_months: Loan tenure in months
            processing_fee_type: Type of processing fee (standard, premium, promotional)
            
        Returns:
            LoanTerms object with all calculated values
        """
        # Calculate EMI
        emi = self.calculate_emi(principal, annual_interest_rate, tenure_months)
        
        # Calculate total amounts
        total_payable = emi * tenure_months
        total_interest = total_payable - principal
        
        # Calculate processing fee
        processing_fee = self._calculate_processing_fee(principal, processing_fee_type)
        
        return LoanTerms(
            amount=principal,
            tenure=tenure_months,
            interest_rate=annual_interest_rate,
            emi=emi,
            total_payable=total_payable,
            total_interest=total_interest,
            processing_fee=processing_fee
        )

    def assess_affordability(self, customer_profile: CustomerProfile, 
                           loan_terms: LoanTerms) -> AffordabilityAssessment:
        """
        Assess loan affordability based on customer's financial profile.
        
        Args:
            customer_profile: Customer's financial profile
            loan_terms: Proposed loan terms
            
        Returns:
            AffordabilityAssessment with detailed analysis
        """
        # Initialize assessment factors
        factors = {
            'has_salary_info': customer_profile.salary is not None,
            'credit_score': customer_profile.credit_score,
            'existing_loans_count': len(customer_profile.current_loans),
            'employment_type': customer_profile.employment_type
        }
        
        # Calculate current debt obligations
        current_emi_burden = sum(loan.emi for loan in customer_profile.current_loans)
        
        if customer_profile.salary:
            # Calculate ratios
            new_emi_ratio = loan_terms.emi / customer_profile.salary
            total_emi_ratio = (current_emi_burden + loan_terms.emi) / customer_profile.salary
            debt_to_income_ratio = customer_profile.calculate_debt_to_income_ratio() or 0
            
            # Available income after existing EMIs
            available_income = customer_profile.get_available_income() or 0
            
            # Maximum affordable EMI (50% of salary minus existing EMIs)
            max_affordable_emi = max(0, (customer_profile.salary * self.max_emi_ratio) - current_emi_burden)
            
            # Calculate maximum affordable loan amount
            max_affordable_amount = self._calculate_max_loan_amount(
                max_affordable_emi, loan_terms.interest_rate, loan_terms.tenure
            )
            
            # Determine affordability
            is_affordable = (
                total_emi_ratio <= self.max_emi_ratio and
                loan_terms.emi <= max_affordable_emi and
                customer_profile.credit_score >= 650  # Minimum credit score
            )
            
            # Determine risk level
            if total_emi_ratio <= self.conservative_emi_ratio:
                risk_level = 'low'
            elif total_emi_ratio <= self.safe_emi_ratio:
                risk_level = 'medium'
            else:
                risk_level = 'high'
            
            # Add detailed factors
            factors.update({
                'new_emi_ratio': new_emi_ratio,
                'total_emi_ratio': total_emi_ratio,
                'current_emi_burden': current_emi_burden,
                'salary': customer_profile.salary,
                'available_income_after_emi': available_income - loan_terms.emi
            })
            
        else:
            # No salary information - conservative assessment
            is_affordable = (
                customer_profile.credit_score >= 700 and
                loan_terms.amount <= customer_profile.pre_approved_limit
            )
            
            new_emi_ratio = 0.0
            total_emi_ratio = 0.0
            available_income = 0.0
            max_affordable_emi = 0.0
            max_affordable_amount = customer_profile.pre_approved_limit
            risk_level = 'medium'  # Default to medium risk without salary info
        
        return AffordabilityAssessment(
            is_affordable=is_affordable,
            emi_to_income_ratio=new_emi_ratio,
            debt_to_income_ratio=total_emi_ratio,
            available_income=available_income,
            max_affordable_emi=max_affordable_emi,
            max_affordable_amount=max_affordable_amount,
            risk_level=risk_level,
            assessment_factors=factors
        )

    def adjust_terms_for_affordability(self, customer_profile: CustomerProfile, 
                                     desired_amount: float, 
                                     interest_rate: float) -> List[LoanTerms]:
        """
        Generate adjusted loan terms to fit customer's affordability.
        
        Args:
            customer_profile: Customer's financial profile
            desired_amount: Desired loan amount
            interest_rate: Interest rate to use
            
        Returns:
            List of adjusted LoanTerms options
        """
        adjusted_options = []
        
        # Get customer's maximum affordable EMI
        if customer_profile.salary:
            current_emi_burden = sum(loan.emi for loan in customer_profile.current_loans)
            max_emi = (customer_profile.salary * self.max_emi_ratio) - current_emi_burden
            safe_emi = (customer_profile.salary * self.safe_emi_ratio) - current_emi_burden
            conservative_emi = (customer_profile.salary * self.conservative_emi_ratio) - current_emi_burden
            
            target_emis = [conservative_emi, safe_emi, max_emi]
        else:
            # Without salary info, use pre-approved limit to estimate EMI capacity
            estimated_emi = customer_profile.pre_approved_limit * 0.02  # Rough 2% of limit
            target_emis = [estimated_emi * 0.8, estimated_emi, estimated_emi * 1.2]
        
        # Generate options for different EMI targets
        for target_emi in target_emis:
            if target_emi <= 0:
                continue
            
            # Option 1: Adjust tenure to fit desired amount
            try:
                required_tenure = self._calculate_tenure_for_emi(
                    desired_amount, interest_rate, target_emi
                )
                
                if self.min_tenure_months <= required_tenure <= self.max_tenure_months:
                    terms = self.calculate_loan_terms(
                        desired_amount, interest_rate, required_tenure
                    )
                    adjusted_options.append(terms)
            except (ValueError, ZeroDivisionError):
                pass
            
            # Option 2: Adjust amount to fit standard tenures
            for tenure in [24, 36, 48, 60, 84, 120]:  # Standard tenure options
                try:
                    max_amount = self._calculate_max_loan_amount(
                        target_emi, interest_rate, tenure
                    )
                    
                    if max_amount >= self.min_loan_amount:
                        # Use the smaller of desired amount or calculated max amount
                        loan_amount = min(desired_amount, max_amount)
                        
                        terms = self.calculate_loan_terms(
                            loan_amount, interest_rate, tenure
                        )
                        
                        # Only add if EMI is within target
                        if terms.emi <= target_emi * 1.05:  # 5% tolerance
                            adjusted_options.append(terms)
                except (ValueError, ZeroDivisionError):
                    continue
        
        # Remove duplicates and sort by amount (descending) then by EMI (ascending)
        unique_options = []
        seen_combinations = set()
        
        for option in adjusted_options:
            key = (round(option.amount), option.tenure, round(option.emi))
            if key not in seen_combinations:
                seen_combinations.add(key)
                unique_options.append(option)
        
        # Sort: higher amount first, then lower EMI
        unique_options.sort(key=lambda x: (-x.amount, x.emi))
        
        return unique_options[:5]  # Return top 5 options

    def validate_loan_terms(self, loan_terms: LoanTerms, 
                          customer_profile: CustomerProfile) -> Dict[str, Any]:
        """
        Validate loan terms against business rules and customer profile.
        
        Args:
            loan_terms: Loan terms to validate
            customer_profile: Customer profile for validation
            
        Returns:
            Validation result with details
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Validate amount limits
        if loan_terms.amount < self.min_loan_amount:
            validation_result['errors'].append(
                f"Loan amount ₹{loan_terms.amount:,.0f} is below minimum ₹{self.min_loan_amount:,.0f}"
            )
            validation_result['is_valid'] = False
        
        if loan_terms.amount > self.max_loan_amount:
            validation_result['errors'].append(
                f"Loan amount ₹{loan_terms.amount:,.0f} exceeds maximum ₹{self.max_loan_amount:,.0f}"
            )
            validation_result['is_valid'] = False
        
        # Validate tenure limits
        if loan_terms.tenure < self.min_tenure_months:
            validation_result['errors'].append(
                f"Tenure {loan_terms.tenure} months is below minimum {self.min_tenure_months} months"
            )
            validation_result['is_valid'] = False
        
        if loan_terms.tenure > self.max_tenure_months:
            validation_result['errors'].append(
                f"Tenure {loan_terms.tenure} months exceeds maximum {self.max_tenure_months} months"
            )
            validation_result['is_valid'] = False
        
        # Validate interest rate
        if loan_terms.interest_rate < self.min_interest_rate:
            validation_result['errors'].append(
                f"Interest rate {loan_terms.interest_rate}% is below minimum {self.min_interest_rate}%"
            )
            validation_result['is_valid'] = False
        
        if loan_terms.interest_rate > self.max_interest_rate:
            validation_result['errors'].append(
                f"Interest rate {loan_terms.interest_rate}% exceeds maximum {self.max_interest_rate}%"
            )
            validation_result['is_valid'] = False
        
        # Validate against customer profile
        if loan_terms.amount > customer_profile.pre_approved_limit * 2:
            validation_result['errors'].append(
                f"Loan amount exceeds 2x pre-approved limit of ₹{customer_profile.pre_approved_limit * 2:,.0f}"
            )
            validation_result['is_valid'] = False
        
        # Credit score validation
        if customer_profile.credit_score < 650:
            validation_result['errors'].append(
                f"Credit score {customer_profile.credit_score} is below minimum requirement of 650"
            )
            validation_result['is_valid'] = False
        
        # Affordability validation
        affordability = self.assess_affordability(customer_profile, loan_terms)
        
        if not affordability.is_affordable:
            validation_result['warnings'].append(
                f"EMI of ₹{loan_terms.emi:,.0f} may exceed customer's repayment capacity"
            )
        
        if affordability.risk_level == 'high':
            validation_result['warnings'].append(
                "High risk: EMI-to-income ratio exceeds safe limits"
            )
        
        # Generate recommendations
        if loan_terms.amount > customer_profile.pre_approved_limit:
            validation_result['recommendations'].append(
                "Consider reducing loan amount to within pre-approved limit for instant approval"
            )
        
        if affordability.emi_to_income_ratio > self.safe_emi_ratio:
            validation_result['recommendations'].append(
                f"Consider extending tenure to reduce EMI below ₹{affordability.max_affordable_emi:,.0f}"
            )
        
        return validation_result

    def calculate_prepayment_scenarios(self, loan_terms: LoanTerms, 
                                     prepayment_amount: float, 
                                     prepayment_month: int) -> Dict[str, Any]:
        """
        Calculate prepayment scenarios and savings.
        
        Args:
            loan_terms: Original loan terms
            prepayment_amount: Amount to prepay
            prepayment_month: Month when prepayment is made
            
        Returns:
            Prepayment analysis with savings calculation
        """
        # Calculate remaining principal at prepayment month
        remaining_principal = self._calculate_remaining_principal(
            loan_terms.amount, loan_terms.interest_rate, 
            loan_terms.emi, prepayment_month
        )
        
        if prepayment_amount > remaining_principal:
            prepayment_amount = remaining_principal
        
        # New principal after prepayment
        new_principal = remaining_principal - prepayment_amount
        
        # Calculate new EMI or new tenure (assuming EMI remains same)
        remaining_tenure = loan_terms.tenure - prepayment_month
        
        if new_principal <= 0:
            # Loan fully paid
            return {
                'loan_closed': True,
                'prepayment_amount': prepayment_amount,
                'interest_saved': self._calculate_future_interest(
                    remaining_principal, loan_terms.interest_rate, 
                    loan_terms.emi, remaining_tenure
                ),
                'new_emi': 0,
                'new_tenure': 0
            }
        
        # Calculate new tenure with same EMI
        try:
            new_tenure = self._calculate_tenure_for_emi(
                new_principal, loan_terms.interest_rate, loan_terms.emi
            )
            
            # Calculate interest saved
            original_future_interest = self._calculate_future_interest(
                remaining_principal, loan_terms.interest_rate, 
                loan_terms.emi, remaining_tenure
            )
            
            new_future_interest = self._calculate_future_interest(
                new_principal, loan_terms.interest_rate, 
                loan_terms.emi, new_tenure
            )
            
            interest_saved = original_future_interest - new_future_interest
            
            return {
                'loan_closed': False,
                'prepayment_amount': prepayment_amount,
                'new_principal': new_principal,
                'new_tenure': int(new_tenure),
                'tenure_reduced_by': remaining_tenure - new_tenure,
                'interest_saved': interest_saved,
                'new_emi': loan_terms.emi  # EMI remains same
            }
            
        except (ValueError, ZeroDivisionError):
            return {
                'error': 'Unable to calculate prepayment scenario',
                'prepayment_amount': prepayment_amount
            }

    # Private helper methods
    
    def _validate_calculation_inputs(self, principal: float, interest_rate: float, 
                                   tenure: int) -> None:
        """Validate inputs for loan calculations"""
        if principal <= 0:
            raise ValueError("Principal amount must be positive")
        
        if interest_rate < 0:
            raise ValueError("Interest rate cannot be negative")
        
        if tenure <= 0:
            raise ValueError("Tenure must be positive")
        
        if principal > self.max_loan_amount:
            raise ValueError(f"Principal exceeds maximum loan amount of ₹{self.max_loan_amount:,.0f}")
        
        if tenure > self.max_tenure_months:
            raise ValueError(f"Tenure exceeds maximum of {self.max_tenure_months} months")

    def _calculate_processing_fee(self, amount: float, fee_type: str = 'standard') -> float:
        """Calculate processing fee based on amount and type"""
        if fee_type not in self.processing_fee_rates:
            fee_type = 'standard'
        
        fee_rate = self.processing_fee_rates[fee_type]
        fee = amount * fee_rate
        
        # Apply maximum fee cap
        return min(fee, self.max_processing_fee)

    def _calculate_max_loan_amount(self, target_emi: float, interest_rate: float, 
                                 tenure: int) -> float:
        """Calculate maximum loan amount for given EMI, rate, and tenure"""
        monthly_rate = interest_rate / (12 * 100)
        
        if monthly_rate == 0:
            return target_emi * tenure
        
        # Reverse EMI formula to get principal
        denominator = monthly_rate * (1 + monthly_rate) ** tenure
        numerator = (1 + monthly_rate) ** tenure - 1
        
        if denominator == 0:
            return 0
        
        max_amount = target_emi * numerator / denominator
        return max_amount

    def _calculate_tenure_for_emi(self, principal: float, interest_rate: float, 
                                target_emi: float) -> int:
        """Calculate required tenure for given principal, rate, and EMI"""
        monthly_rate = interest_rate / (12 * 100)
        
        if monthly_rate == 0:
            return int(principal / target_emi)
        
        if target_emi <= principal * monthly_rate:
            raise ValueError("EMI too low to cover interest")
        
        # Use logarithmic formula to solve for tenure
        numerator = math.log(1 + (principal * monthly_rate / target_emi))
        denominator = math.log(1 + monthly_rate)
        
        tenure = -numerator / denominator
        return int(math.ceil(tenure))

    def _calculate_remaining_principal(self, original_principal: float, 
                                     interest_rate: float, emi: float, 
                                     months_paid: int) -> float:
        """Calculate remaining principal after specified months"""
        monthly_rate = interest_rate / (12 * 100)
        
        if monthly_rate == 0:
            return max(0, original_principal - (emi * months_paid))
        
        # Calculate remaining principal using amortization formula
        remaining = original_principal * (1 + monthly_rate) ** months_paid
        remaining -= emi * (((1 + monthly_rate) ** months_paid - 1) / monthly_rate)
        
        return max(0, remaining)

    def _calculate_future_interest(self, principal: float, interest_rate: float, 
                                 emi: float, remaining_months: int) -> float:
        """Calculate total interest for remaining tenure"""
        total_payments = emi * remaining_months
        return max(0, total_payments - principal)