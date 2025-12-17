#!/usr/bin/env python3
"""
Simple PDF Generation Test
"""

from services.sanction_letter_generator import SanctionLetterGenerator
from models.loan import LoanApplication, LoanStatus
from models.customer import CustomerProfile
import uuid

def test_simple_pdf():
    """Test simple PDF generation"""
    try:
        # Create test data
        customer = CustomerProfile(
            id=str(uuid.uuid4()),
            name="John Doe",
            age=35,
            city="Mumbai",
            phone="9876543210",
            address="Mumbai, Maharashtra",
            salary=80000.0,
            credit_score=750,
            pre_approved_limit=500000.0,
            employment_type="salaried"
        )
        
        loan = LoanApplication(
            id=str(uuid.uuid4()),
            customer_id=customer.id,
            requested_amount=300000.0,
            tenure=60,
            interest_rate=12.5,
            emi=6700.0,
            status=LoanStatus.APPROVED
        )
        
        # Generate PDF
        generator = SanctionLetterGenerator()
        filepath = generator.generate_sanction_letter(loan, customer)
        
        print(f"PDF generated successfully: {filepath}")
        return True
        
    except Exception as e:
        print(f"PDF generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_pdf()
    print(f"Simple PDF Test: {'PASS' if success else 'FAIL'}")