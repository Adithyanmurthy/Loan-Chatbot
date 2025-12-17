"""
Demo Verification Service
Simulates a realistic KYC verification process for demonstration purposes
"""

import random
import time
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VerificationStep:
    """Represents a single verification step"""
    name: str
    status: str  # pending, in_progress, verified, failed
    message: str
    confidence: float
    timestamp: datetime


class DemoVerificationService:
    """
    Demo verification service that simulates realistic KYC verification
    without actual external API calls
    """
    
    def __init__(self):
        self.verification_delay = 1.5  # Simulated processing time
        
        # Demo verification rules
        self.valid_name_patterns = ['kumar', 'sharma', 'patel', 'singh', 'gupta', 
                                    'reddy', 'nair', 'iyer', 'joshi', 'malhotra']
        
        # Demo phone prefixes (Indian mobile)
        self.valid_phone_prefixes = ['6', '7', '8', '9']

    def perform_full_verification(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform complete KYC verification (demo mode)
        
        Args:
            customer_data: Customer information to verify
            
        Returns:
            Complete verification result with all steps
        """
        verification_id = f"VER_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8].upper()}"
        
        logger.info(f"Starting demo verification: {verification_id}")
        
        # Simulate processing delay
        time.sleep(self.verification_delay)
        
        steps = []
        overall_score = 0
        
        # Step 1: Name Verification
        name_result = self._verify_name(customer_data.get('name', ''))
        steps.append(name_result)
        overall_score += name_result['score']
        
        # Step 2: Phone Verification
        phone_result = self._verify_phone(customer_data.get('phone', ''))
        steps.append(phone_result)
        overall_score += phone_result['score']
        
        # Step 3: Address Verification
        address_result = self._verify_address(customer_data.get('address', ''), customer_data.get('city', ''))
        steps.append(address_result)
        overall_score += address_result['score']
        
        # Step 4: Age Verification
        age_result = self._verify_age(customer_data.get('age'))
        steps.append(age_result)
        overall_score += age_result['score']
        
        # Step 5: Employment Verification
        employment_result = self._verify_employment(
            customer_data.get('employment_type', ''),
            customer_data.get('salary')
        )
        steps.append(employment_result)
        overall_score += employment_result['score']
        
        # Calculate overall result
        avg_score = overall_score / len(steps)
        is_verified = avg_score >= 70
        
        # Determine verification status
        failed_steps = [s for s in steps if s['status'] == 'failed']
        
        if len(failed_steps) >= 2:
            overall_status = 'failed'
            verification_message = "Verification failed. Multiple checks did not pass."
        elif len(failed_steps) == 1:
            overall_status = 'partial'
            verification_message = f"Partial verification. {failed_steps[0]['name']} verification needs attention."
        else:
            overall_status = 'verified'
            verification_message = "All verification checks passed successfully!"

        return {
            'verification_id': verification_id,
            'overall_status': overall_status,
            'is_verified': is_verified,
            'verification_score': round(avg_score, 1),
            'message': verification_message,
            'steps': steps,
            'customer_data': {
                'name': customer_data.get('name'),
                'phone': self._mask_phone(customer_data.get('phone', '')),
                'city': customer_data.get('city'),
                'age': customer_data.get('age')
            },
            'verified_at': datetime.now().isoformat(),
            'demo_mode': True
        }
    
    def _verify_name(self, name: str) -> Dict[str, Any]:
        """Verify customer name"""
        if not name or len(name.strip()) < 2:
            return {
                'name': 'Name Verification',
                'status': 'failed',
                'message': 'Name is required and must be at least 2 characters',
                'score': 0
            }
        
        name_lower = name.lower().strip()
        
        # Check for valid name patterns (demo logic)
        has_valid_pattern = any(pattern in name_lower for pattern in self.valid_name_patterns)
        has_space = ' ' in name_lower  # Full name check
        
        if has_valid_pattern or has_space:
            return {
                'name': 'Name Verification',
                'status': 'verified',
                'message': f'Name "{name}" verified successfully',
                'score': 100
            }
        elif len(name_lower) >= 3:
            return {
                'name': 'Name Verification',
                'status': 'verified',
                'message': f'Name "{name}" accepted',
                'score': 85
            }
        else:
            return {
                'name': 'Name Verification',
                'status': 'failed',
                'message': 'Please provide your full name',
                'score': 30
            }
    
    def _verify_phone(self, phone: str) -> Dict[str, Any]:
        """Verify phone number"""
        if not phone:
            return {
                'name': 'Phone Verification',
                'status': 'failed',
                'message': 'Phone number is required',
                'score': 0
            }
        
        # Clean phone number
        digits = ''.join(filter(str.isdigit, phone))
        
        # Remove country code if present
        if digits.startswith('91') and len(digits) == 12:
            digits = digits[2:]
        
        if len(digits) == 10 and digits[0] in self.valid_phone_prefixes:
            return {
                'name': 'Phone Verification',
                'status': 'verified',
                'message': f'Phone number verified (ending in {digits[-4:]})',
                'score': 100
            }
        elif len(digits) == 10:
            return {
                'name': 'Phone Verification',
                'status': 'verified',
                'message': 'Phone number format accepted',
                'score': 80
            }
        else:
            return {
                'name': 'Phone Verification',
                'status': 'failed',
                'message': 'Invalid phone number format. Please provide 10-digit mobile number',
                'score': 20
            }

    def _verify_address(self, address: str, city: str) -> Dict[str, Any]:
        """Verify address"""
        if not address and not city:
            return {
                'name': 'Address Verification',
                'status': 'failed',
                'message': 'Address information is required',
                'score': 0
            }
        
        # Valid Indian cities for demo
        valid_cities = ['mumbai', 'delhi', 'bangalore', 'hyderabad', 'chennai', 
                       'kolkata', 'pune', 'ahmedabad', 'jaipur', 'lucknow',
                       'kochi', 'chandigarh', 'indore', 'bhopal', 'nagpur']
        
        city_lower = (city or '').lower().strip()
        address_lower = (address or '').lower().strip()
        
        city_valid = any(c in city_lower or c in address_lower for c in valid_cities)
        address_valid = len(address_lower) >= 10 if address_lower else False
        
        if city_valid and address_valid:
            return {
                'name': 'Address Verification',
                'status': 'verified',
                'message': f'Address in {city or "provided location"} verified',
                'score': 100
            }
        elif city_valid or address_valid:
            return {
                'name': 'Address Verification',
                'status': 'verified',
                'message': 'Address information accepted',
                'score': 75
            }
        else:
            return {
                'name': 'Address Verification',
                'status': 'partial',
                'message': 'Address verification pending - please provide complete address',
                'score': 50
            }
    
    def _verify_age(self, age: Any) -> Dict[str, Any]:
        """Verify age eligibility"""
        if age is None:
            return {
                'name': 'Age Verification',
                'status': 'partial',
                'message': 'Age not provided - will be verified during documentation',
                'score': 60
            }
        
        try:
            age_int = int(age)
            if 21 <= age_int <= 65:
                return {
                    'name': 'Age Verification',
                    'status': 'verified',
                    'message': f'Age {age_int} is within eligible range (21-65)',
                    'score': 100
                }
            elif 18 <= age_int < 21:
                return {
                    'name': 'Age Verification',
                    'status': 'partial',
                    'message': f'Age {age_int} - minimum age for loan is 21 years',
                    'score': 40
                }
            elif age_int > 65:
                return {
                    'name': 'Age Verification',
                    'status': 'failed',
                    'message': f'Age {age_int} exceeds maximum eligible age of 65',
                    'score': 20
                }
            else:
                return {
                    'name': 'Age Verification',
                    'status': 'failed',
                    'message': 'Invalid age provided',
                    'score': 0
                }
        except (ValueError, TypeError):
            return {
                'name': 'Age Verification',
                'status': 'partial',
                'message': 'Age format not recognized',
                'score': 50
            }

    def _verify_employment(self, employment_type: str, salary: Any) -> Dict[str, Any]:
        """Verify employment information"""
        valid_types = ['salaried', 'self_employed', 'business', 'professional', 'government']
        
        emp_lower = (employment_type or '').lower().strip()
        
        if not emp_lower:
            return {
                'name': 'Employment Verification',
                'status': 'partial',
                'message': 'Employment type not specified',
                'score': 50
            }
        
        type_valid = any(t in emp_lower for t in valid_types)
        
        salary_valid = False
        salary_score = 0
        if salary:
            try:
                salary_float = float(salary)
                if salary_float >= 15000:
                    salary_valid = True
                    salary_score = 50
            except (ValueError, TypeError):
                pass
        
        if type_valid and salary_valid:
            return {
                'name': 'Employment Verification',
                'status': 'verified',
                'message': f'Employment ({employment_type}) and income verified',
                'score': 100
            }
        elif type_valid:
            return {
                'name': 'Employment Verification',
                'status': 'verified',
                'message': f'Employment type ({employment_type}) verified',
                'score': 75
            }
        else:
            return {
                'name': 'Employment Verification',
                'status': 'partial',
                'message': 'Employment verification pending',
                'score': 50
            }
    
    def _mask_phone(self, phone: str) -> str:
        """Mask phone number for privacy"""
        if not phone:
            return ''
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) >= 10:
            return f"XXXXXX{digits[-4:]}"
        return phone
    
    def get_verification_status_message(self, verification_result: Dict[str, Any]) -> str:
        """Generate a user-friendly verification status message"""
        status = verification_result.get('overall_status', 'unknown')
        score = verification_result.get('verification_score', 0)
        
        if status == 'verified':
            return f"""✅ **KYC Verification Successful!**

Your identity has been verified with a confidence score of {score}%.

**Verified Details:**
• Name: {verification_result.get('customer_data', {}).get('name', 'N/A')}
• Phone: {verification_result.get('customer_data', {}).get('phone', 'N/A')}
• City: {verification_result.get('customer_data', {}).get('city', 'N/A')}

We can now proceed with your loan application."""
        
        elif status == 'partial':
            return f"""⚠️ **Partial Verification**

Some verification checks need attention (Score: {score}%).

Please ensure all your details are correct. We may request additional documents during the process."""
        
        else:
            return f"""❌ **Verification Incomplete**

We couldn't fully verify your details (Score: {score}%).

Please check your information and try again, or contact support for assistance."""


# Global instance
_demo_verification_service: Optional[DemoVerificationService] = None

def get_demo_verification_service() -> DemoVerificationService:
    """Get or create the demo verification service singleton"""
    global _demo_verification_service
    if _demo_verification_service is None:
        _demo_verification_service = DemoVerificationService()
    return _demo_verification_service
