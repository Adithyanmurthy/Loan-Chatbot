"""
Verification Agent for AI Loan Chatbot
Implements KYC validation against CRM server, phone and address verification logic,
and verification failure handling with documentation requests.
Based on requirements: 3.1, 3.2, 3.3, 3.4
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from .base_agent import BaseAgent
from models.conversation import AgentType, TaskType, AgentTask
from models.customer import CustomerProfile
from services.crm_client import CRMClient, CRMResponse, CRMErrorType
from services.verification_tracker import (
    VerificationTracker, VerificationRecord, VerificationStatusType, 
    VerificationMethod, get_verification_tracker
)
from services.demo_verification_service import get_demo_verification_service


class VerificationStatus:
    """Enumeration for verification status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    FAILED = "failed"
    REQUIRES_DOCUMENTS = "requires_documents"


class VerificationResult:
    """Class to hold verification results"""
    def __init__(self, status: str, details: Dict[str, Any], issues: List[str] = None):
        self.status = status
        self.details = details
        self.issues = issues or []
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "details": self.details,
            "issues": self.issues,
            "timestamp": self.timestamp.isoformat()
        }


class VerificationAgent(BaseAgent):
    """
    Verification Agent responsible for KYC validation, phone and address verification.
    Handles verification failures and requests additional documentation when needed.
    """

    def __init__(self, agent_id: Optional[str] = None, crm_base_url: str = "http://localhost:3001"):
        """
        Initialize Verification Agent.
        
        Args:
            agent_id: Optional unique identifier for the agent
            crm_base_url: Base URL for CRM API server
        """
        super().__init__(AgentType.VERIFICATION, agent_id)
        
        # Initialize CRM client and verification tracker
        self.crm_client = CRMClient(base_url=crm_base_url)
        self.verification_tracker = get_verification_tracker()
        
        # Verification configuration
        self.verification_timeout = 30  # seconds
        self.max_retry_attempts = 3
        self.retry_delay = 2  # seconds
        
        # Verification thresholds and rules
        self.phone_validation_rules = {
            'min_length': 10,
            'max_length': 13,
            'allowed_prefixes': ['+91', '91', '0']
        }
        
        self.address_validation_rules = {
            'min_length': 10,
            'required_components': ['street', 'city', 'state', 'pincode']
        }
        
        self.logger.info(f"Verification Agent initialized with CRM client and verification tracker")

    def can_execute_task(self, task_type: TaskType) -> bool:
        """
        Check if this agent can execute verification tasks.
        
        Args:
            task_type: Type of task to check
            
        Returns:
            True if agent can execute verification tasks
        """
        return task_type == TaskType.VERIFICATION

    def _execute_task_logic(self, task: AgentTask) -> Dict[str, Any]:
        """
        Execute verification task logic based on task input.
        
        Args:
            task: AgentTask containing verification parameters
            
        Returns:
            Verification results
        """
        task_input = task.input
        verification_type = task_input.get('verification_type', 'full_kyc')
        
        self.logger.info(f"Executing verification task: {verification_type}")
        
        if verification_type == 'full_kyc':
            return self._perform_enhanced_kyc_verification(task_input)
        elif verification_type == 'phone_verification':
            return self._perform_phone_verification(task_input)
        elif verification_type == 'address_verification':
            return self._perform_address_verification(task_input)
        elif verification_type == 'document_verification':
            return self._perform_document_verification(task_input)
        else:
            raise ValueError(f"Unknown verification type: {verification_type}")
    
    def _perform_enhanced_kyc_verification(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform enhanced KYC verification using the demo verification service.
        
        Args:
            task_input: Dictionary containing customer_id and provided_details
            
        Returns:
            Enhanced verification results with detailed status
        """
        customer_id = task_input.get('customer_id', 'GUEST_USER')
        provided_details = task_input.get('provided_details', {})
        session_id = task_input.get('session_id', 'default_session')
        
        self.logger.info(f"Starting enhanced KYC verification for customer: {customer_id}")
        
        # Use the demo verification service for realistic simulation
        demo_service = get_demo_verification_service()
        
        # Prepare customer data for verification
        customer_data = {
            'name': provided_details.get('name', ''),
            'phone': provided_details.get('phone', ''),
            'address': provided_details.get('address', ''),
            'city': provided_details.get('city', ''),
            'age': provided_details.get('age'),
            'employment_type': provided_details.get('employment_type', 'salaried'),
            'salary': provided_details.get('salary')
        }
        
        # Perform verification using demo service
        demo_result = demo_service.perform_full_verification(customer_data)
        
        # Convert demo result to expected format
        is_verified = demo_result.get('is_verified', False)
        verification_score = demo_result.get('verification_score', 0)
        steps = demo_result.get('steps', [])
        
        if is_verified:
            # Build verification details from steps
            verification_details = {}
            for step in steps:
                step_name = step.get('name', '').lower().replace(' verification', '')
                status_icon = '✅' if step.get('status') == 'verified' else '⚠️'
                verification_details[f'{step_name}_match'] = f"{step.get('message', 'Checked')} {status_icon}"
            
            verification_details['risk_assessment'] = 'Low Risk'
            verification_details['verification_method'] = 'Automated KYC (Demo)'
            
            verification_result = {
                'verification_successful': True,
                'verification_score': verification_score,
                'customer_id': customer_id,
                'verified_fields': ['name', 'phone', 'address', 'age', 'employment'],
                'verification_details': verification_details,
                'verification_steps': steps,
                'next_action': 'proceed_to_underwriting',
                'message': demo_service.get_verification_status_message(demo_result)
            }
            
            # Share verification success with context
            if self.context:
                self.share_context_data('kyc_verified', True)
                self.share_context_data('verification_score', verification_score)
                self.share_context_data('verification_details', verification_result)
            
            return verification_result
            
        else:
            # Verification failed or partial - determine required documents
            failed_steps = [s for s in steps if s.get('status') == 'failed']
            partial_steps = [s for s in steps if s.get('status') == 'partial']
            
            missing_docs = []
            for step in failed_steps + partial_steps:
                step_name = step.get('name', '').lower()
                if 'name' in step_name or 'identity' in step_name:
                    missing_docs.extend(['aadhaar_card', 'pan_card'])
                elif 'address' in step_name:
                    missing_docs.append('address_proof')
                elif 'employment' in step_name:
                    missing_docs.append('salary_slip')
            
            # Remove duplicates
            missing_docs = list(set(missing_docs)) or ['identity_proof']
            
            verification_result = {
                'verification_successful': False,
                'requires_documents': True,
                'customer_id': customer_id,
                'verification_score': verification_score,
                'missing_documents': missing_docs,
                'verification_steps': steps,
                'verification_details': {
                    'overall_status': demo_result.get('overall_status', 'partial'),
                    'verification_method': 'Manual Review Required'
                },
                'next_action': 'request_documents',
                'message': demo_service.get_verification_status_message(demo_result)
            }
            
            return verification_result

    def _perform_full_kyc_verification(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive KYC verification against CRM server.
        Validates customer details, phone, and address information.
        
        Args:
            task_input: Dictionary containing customer_id and provided_details
            
        Returns:
            Comprehensive verification results
        """
        customer_id = task_input.get('customer_id')
        provided_details = task_input.get('provided_details', {})
        session_id = task_input.get('session_id', 'default_session')
        
        if not customer_id:
            raise ValueError("Customer ID is required for KYC verification")
        
        self.logger.info(f"Starting full KYC verification for customer: {customer_id}")
        
        # Start verification tracking
        verification_record = self.verification_tracker.start_verification(
            customer_id=customer_id,
            session_id=session_id,
            method=VerificationMethod.AUTOMATIC_CRM
        )
        
        # Fetch customer data from CRM using the new client
        crm_response = self.crm_client.get_customer_data(customer_id)
        
        if not crm_response.success:
            # Update verification tracker with failure
            self.verification_tracker.update_verification(
                customer_id=customer_id,
                session_id=session_id,
                status=VerificationStatusType.FAILED,
                issues=[f"CRM error: {crm_response.error}"],
                metadata={"crm_error_type": crm_response.error_type.value if crm_response.error_type else "unknown"}
            )
            
            return {
                "verification_result": VerificationResult(
                    status=VerificationStatus.FAILED,
                    details={"error": f"Unable to fetch customer data from CRM: {crm_response.error}"},
                    issues=[f"CRM data unavailable: {crm_response.error}"]
                ).to_dict(),
                "next_action": "request_manual_verification",
                "message": "We're unable to verify your details automatically. Please provide additional documentation."
            }
        
        crm_data = crm_response.data
        
        # Perform individual verifications
        phone_result = self._verify_phone_details(provided_details.get('phone'), crm_data.get('phone'))
        address_result = self._verify_address_details(provided_details.get('address'), crm_data.get('address'))
        personal_result = self._verify_personal_details(provided_details, crm_data)
        
        # Aggregate results
        all_results = [phone_result, address_result, personal_result]
        failed_verifications = [r for r in all_results if r.status == VerificationStatus.FAILED]
        
        if failed_verifications:
            # Some verifications failed
            all_issues = []
            for result in failed_verifications:
                all_issues.extend(result.issues)
            
            # Update verification tracker with failure
            self.verification_tracker.update_verification(
                customer_id=customer_id,
                session_id=session_id,
                status=VerificationStatusType.REQUIRES_DOCUMENTS,
                issues=all_issues,
                required_documents=self._determine_required_documents(all_issues),
                verification_score=self._calculate_verification_score(all_results),
                metadata={
                    "phone_verified": phone_result.status == VerificationStatus.VERIFIED,
                    "address_verified": address_result.status == VerificationStatus.VERIFIED,
                    "personal_verified": personal_result.status == VerificationStatus.VERIFIED
                }
            )
            
            overall_result = VerificationResult(
                status=VerificationStatus.REQUIRES_DOCUMENTS,
                details={
                    "phone_verification": phone_result.to_dict(),
                    "address_verification": address_result.to_dict(),
                    "personal_verification": personal_result.to_dict(),
                    "crm_data": crm_data
                },
                issues=all_issues
            )
            
            return {
                "verification_result": overall_result.to_dict(),
                "next_action": "request_additional_documents",
                "message": self._generate_verification_failure_message(all_issues),
                "required_documents": self._determine_required_documents(all_issues)
            }
        else:
            # All verifications passed
            verification_score = self._calculate_verification_score(all_results)
            
            # Update verification tracker with success
            self.verification_tracker.update_verification(
                customer_id=customer_id,
                session_id=session_id,
                status=VerificationStatusType.VERIFIED,
                verification_score=verification_score,
                verified_fields=['phone', 'address', 'personal_details'],
                metadata={
                    "phone_verified": True,
                    "address_verified": True,
                    "personal_verified": True,
                    "crm_response_time": crm_response.response_time
                }
            )
            
            overall_result = VerificationResult(
                status=VerificationStatus.VERIFIED,
                details={
                    "phone_verification": phone_result.to_dict(),
                    "address_verification": address_result.to_dict(),
                    "personal_verification": personal_result.to_dict(),
                    "crm_data": crm_data,
                    "verification_score": verification_score
                }
            )
            
            # Share verification success with context
            if self.context:
                self.share_context_data('kyc_verified', True)
                self.share_context_data('verification_details', overall_result.to_dict())
            
            return {
                "verification_result": overall_result.to_dict(),
                "next_action": "proceed_to_underwriting",
                "message": "Great! Your identity has been successfully verified. We can now proceed with your loan application."
            }

    def _perform_phone_verification(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform phone number verification against CRM data.
        
        Args:
            task_input: Dictionary containing customer_id and phone number
            
        Returns:
            Phone verification results
        """
        customer_id = task_input.get('customer_id')
        provided_phone = task_input.get('phone')
        
        crm_response = self.crm_client.get_customer_data(customer_id)
        if not crm_response.success:
            return {
                "verification_result": VerificationResult(
                    status=VerificationStatus.FAILED,
                    details={"error": f"CRM data unavailable: {crm_response.error}"},
                    issues=["Unable to fetch customer data"]
                ).to_dict()
            }
        
        result = self._verify_phone_details(provided_phone, crm_response.data.get('phone'))
        return {"verification_result": result.to_dict()}

    def _perform_address_verification(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform address verification against CRM data.
        
        Args:
            task_input: Dictionary containing customer_id and address
            
        Returns:
            Address verification results
        """
        customer_id = task_input.get('customer_id')
        provided_address = task_input.get('address')
        
        crm_response = self.crm_client.get_customer_data(customer_id)
        if not crm_response.success:
            return {
                "verification_result": VerificationResult(
                    status=VerificationStatus.FAILED,
                    details={"error": f"CRM data unavailable: {crm_response.error}"},
                    issues=["Unable to fetch customer data"]
                ).to_dict()
            }
        
        result = self._verify_address_details(provided_address, crm_response.data.get('address'))
        return {"verification_result": result.to_dict()}

    def _perform_document_verification(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform document-based verification when automatic verification fails.
        
        Args:
            task_input: Dictionary containing document information
            
        Returns:
            Document verification results
        """
        documents = task_input.get('documents', [])
        customer_id = task_input.get('customer_id')
        
        if not documents:
            return {
                "verification_result": VerificationResult(
                    status=VerificationStatus.FAILED,
                    details={"error": "No documents provided"},
                    issues=["Documents required for verification"]
                ).to_dict(),
                "message": "Please upload the required documents to complete verification."
            }
        
        # Simulate document verification process
        # In a real implementation, this would involve OCR and document analysis
        verification_score = 0
        verified_documents = []
        
        for doc in documents:
            doc_type = doc.get('type')
            doc_status = self._verify_document(doc)
            
            if doc_status['valid']:
                verification_score += doc_status['score']
                verified_documents.append(doc_type)
        
        if verification_score >= 80:  # Threshold for successful verification
            result = VerificationResult(
                status=VerificationStatus.VERIFIED,
                details={
                    "verification_score": verification_score,
                    "verified_documents": verified_documents,
                    "document_count": len(documents)
                }
            )
            
            if self.context:
                self.share_context_data('kyc_verified', True)
                self.share_context_data('verification_method', 'document_based')
            
            return {
                "verification_result": result.to_dict(),
                "next_action": "proceed_to_underwriting",
                "message": "Thank you! Your documents have been verified successfully."
            }
        else:
            result = VerificationResult(
                status=VerificationStatus.FAILED,
                details={
                    "verification_score": verification_score,
                    "verified_documents": verified_documents,
                    "required_score": 80
                },
                issues=["Insufficient document verification score"]
            )
            
            return {
                "verification_result": result.to_dict(),
                "next_action": "request_additional_documents",
                "message": "We need additional documents to complete your verification. Please upload clear copies of the required documents."
            }



    def _verify_phone_details(self, provided_phone: str, crm_phone: str) -> VerificationResult:
        """
        Verify phone number against CRM data.
        
        Args:
            provided_phone: Phone number provided by customer
            crm_phone: Phone number from CRM system
            
        Returns:
            VerificationResult for phone verification
        """
        if not provided_phone or not crm_phone:
            return VerificationResult(
                status=VerificationStatus.FAILED,
                details={"provided": provided_phone, "crm": crm_phone},
                issues=["Missing phone number data"]
            )
        
        # Normalize phone numbers for comparison
        normalized_provided = self._normalize_phone_number(provided_phone)
        normalized_crm = self._normalize_phone_number(crm_phone)
        
        if normalized_provided == normalized_crm:
            return VerificationResult(
                status=VerificationStatus.VERIFIED,
                details={
                    "provided": provided_phone,
                    "crm": crm_phone,
                    "normalized_match": True
                }
            )
        else:
            return VerificationResult(
                status=VerificationStatus.FAILED,
                details={
                    "provided": provided_phone,
                    "crm": crm_phone,
                    "normalized_provided": normalized_provided,
                    "normalized_crm": normalized_crm
                },
                issues=["Phone number mismatch"]
            )

    def _verify_address_details(self, provided_address: str, crm_address: str) -> VerificationResult:
        """
        Verify address against CRM data.
        
        Args:
            provided_address: Address provided by customer
            crm_address: Address from CRM system
            
        Returns:
            VerificationResult for address verification
        """
        if not provided_address or not crm_address:
            return VerificationResult(
                status=VerificationStatus.FAILED,
                details={"provided": provided_address, "crm": crm_address},
                issues=["Missing address data"]
            )
        
        # Calculate address similarity score
        similarity_score = self._calculate_address_similarity(provided_address, crm_address)
        
        if similarity_score >= 0.8:  # 80% similarity threshold
            return VerificationResult(
                status=VerificationStatus.VERIFIED,
                details={
                    "provided": provided_address,
                    "crm": crm_address,
                    "similarity_score": similarity_score
                }
            )
        else:
            return VerificationResult(
                status=VerificationStatus.FAILED,
                details={
                    "provided": provided_address,
                    "crm": crm_address,
                    "similarity_score": similarity_score,
                    "threshold": 0.8
                },
                issues=["Address mismatch"]
            )

    def _verify_personal_details(self, provided_details: Dict[str, Any], crm_data: Dict[str, Any]) -> VerificationResult:
        """
        Verify personal details like name, age, etc.
        
        Args:
            provided_details: Details provided by customer
            crm_data: Data from CRM system
            
        Returns:
            VerificationResult for personal details verification
        """
        issues = []
        details = {}
        
        # Verify name
        provided_name = provided_details.get('name', '').strip().lower()
        crm_name = crm_data.get('name', '').strip().lower()
        
        if provided_name and crm_name:
            name_similarity = self._calculate_name_similarity(provided_name, crm_name)
            details['name_verification'] = {
                "provided": provided_details.get('name'),
                "crm": crm_data.get('name'),
                "similarity": name_similarity
            }
            
            if name_similarity < 0.7:  # 70% similarity threshold for names
                issues.append("Name mismatch")
        
        # Verify age (if provided)
        if 'age' in provided_details and 'age' in crm_data:
            age_diff = abs(provided_details['age'] - crm_data['age'])
            details['age_verification'] = {
                "provided": provided_details['age'],
                "crm": crm_data['age'],
                "difference": age_diff
            }
            
            if age_diff > 2:  # Allow 2 years difference
                issues.append("Age mismatch")
        
        if issues:
            return VerificationResult(
                status=VerificationStatus.FAILED,
                details=details,
                issues=issues
            )
        else:
            return VerificationResult(
                status=VerificationStatus.VERIFIED,
                details=details
            )

    def _normalize_phone_number(self, phone: str) -> str:
        """
        Normalize phone number for comparison.
        
        Args:
            phone: Raw phone number string
            
        Returns:
            Normalized phone number
        """
        if not phone:
            return ""
        
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, phone))
        
        # Handle Indian phone numbers
        if digits_only.startswith('91') and len(digits_only) == 12:
            return digits_only[2:]  # Remove country code
        elif digits_only.startswith('0') and len(digits_only) == 11:
            return digits_only[1:]  # Remove leading zero
        elif len(digits_only) == 10:
            return digits_only
        
        return digits_only

    def _calculate_address_similarity(self, addr1: str, addr2: str) -> float:
        """
        Calculate similarity score between two addresses.
        
        Args:
            addr1: First address string
            addr2: Second address string
            
        Returns:
            Similarity score between 0 and 1
        """
        if not addr1 or not addr2:
            return 0.0
        
        # Simple token-based similarity
        tokens1 = set(addr1.lower().split())
        tokens2 = set(addr2.lower().split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        return len(intersection) / len(union) if union else 0.0

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity score between two names.
        
        Args:
            name1: First name string
            name2: Second name string
            
        Returns:
            Similarity score between 0 and 1
        """
        if not name1 or not name2:
            return 0.0
        
        # Simple word-based similarity for names
        words1 = set(name1.lower().split())
        words2 = set(name2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0

    def _verify_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify a single document (simulated).
        
        Args:
            document: Document information
            
        Returns:
            Document verification status and score
        """
        doc_type = document.get('type', '').lower()
        
        # Simulate document verification scores based on type
        verification_scores = {
            'aadhaar': 40,
            'pan': 35,
            'passport': 45,
            'driving_license': 30,
            'voter_id': 25,
            'utility_bill': 20,
            'bank_statement': 25
        }
        
        base_score = verification_scores.get(doc_type, 10)
        
        # Add some randomness to simulate real verification
        import random
        score_variation = random.randint(-5, 10)
        final_score = max(0, min(50, base_score + score_variation))
        
        return {
            'valid': final_score > 15,
            'score': final_score,
            'type': doc_type
        }

    def _calculate_verification_score(self, results: List[VerificationResult]) -> int:
        """
        Calculate overall verification score from individual results.
        
        Args:
            results: List of verification results
            
        Returns:
            Overall verification score (0-100)
        """
        if not results:
            return 0
        
        verified_count = sum(1 for r in results if r.status == VerificationStatus.VERIFIED)
        return int((verified_count / len(results)) * 100)

    def _generate_verification_failure_message(self, issues: List[str]) -> str:
        """
        Generate user-friendly message for verification failures.
        
        Args:
            issues: List of verification issues
            
        Returns:
            User-friendly error message
        """
        if not issues:
            return "We encountered some issues during verification. Please provide additional documentation."
        
        if len(issues) == 1:
            issue = issues[0].lower()
            if 'phone' in issue:
                return "We couldn't verify your phone number. Please ensure you've provided the correct number registered with us."
            elif 'address' in issue:
                return "We couldn't verify your address. Please confirm your current address matches our records."
            elif 'name' in issue:
                return "We couldn't verify your name. Please ensure it matches exactly with your official documents."
            else:
                return f"We encountered an issue with your {issue}. Please provide additional documentation."
        else:
            return "We couldn't verify some of your details automatically. Please provide additional documentation to complete the verification process."

    def _determine_required_documents(self, issues: List[str]) -> List[str]:
        """
        Determine what documents are required based on verification issues.
        
        Args:
            issues: List of verification issues
            
        Returns:
            List of required document types
        """
        required_docs = []
        
        for issue in issues:
            issue_lower = issue.lower()
            if 'phone' in issue_lower:
                required_docs.extend(['utility_bill', 'bank_statement'])
            elif 'address' in issue_lower:
                required_docs.extend(['utility_bill', 'aadhaar', 'passport'])
            elif 'name' in issue_lower:
                required_docs.extend(['aadhaar', 'pan', 'passport'])
        
        # Remove duplicates and add basic identity documents
        required_docs = list(set(required_docs))
        if not required_docs:
            required_docs = ['aadhaar', 'pan']
        
        return required_docs

    def get_verification_status(self, customer_id: str, session_id: str = None) -> Dict[str, Any]:
        """
        Get current verification status for a customer.
        
        Args:
            customer_id: Customer identifier
            session_id: Optional session identifier
            
        Returns:
            Current verification status
        """
        # Try to get status from verification tracker first
        if session_id:
            verification_record = self.verification_tracker.get_verification_status(customer_id, session_id)
            if verification_record:
                return {
                    "customer_id": customer_id,
                    "session_id": session_id,
                    "verified": verification_record.status == VerificationStatusType.VERIFIED,
                    "status": verification_record.status.value,
                    "verification_score": verification_record.verification_score,
                    "verified_fields": verification_record.verified_fields,
                    "issues": verification_record.issues,
                    "last_updated": verification_record.last_attempt_at.isoformat() if verification_record.last_attempt_at else None,
                    "expires_at": verification_record.expires_at.isoformat() if verification_record.expires_at else None
                }
        
        # Check if customer has any valid verification
        is_verified = self.verification_tracker.is_customer_verified(customer_id)
        latest_verification = self.verification_tracker.get_latest_verification(customer_id)
        
        # Fallback to context data if available
        if self.context and self.context.customer_id == customer_id:
            kyc_verified = self.get_shared_data('kyc_verified')
            verification_details = self.get_shared_data('verification_details')
            
            return {
                "customer_id": customer_id,
                "verified": kyc_verified or is_verified,
                "details": verification_details,
                "latest_verification": latest_verification.to_dict() if latest_verification else None,
                "last_updated": datetime.now().isoformat()
            }
        
        return {
            "customer_id": customer_id,
            "verified": is_verified,
            "latest_verification": latest_verification.to_dict() if latest_verification else None,
            "last_updated": latest_verification.last_attempt_at.isoformat() if latest_verification and latest_verification.last_attempt_at else None
        }
    
    def get_crm_health_status(self) -> Dict[str, Any]:
        """
        Get health status of CRM integration.
        
        Returns:
            CRM health status information
        """
        return self.crm_client.get_health_status()
    
    def get_verification_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get verification statistics for reporting.
        
        Args:
            days: Number of days to include in statistics
            
        Returns:
            Verification statistics
        """
        return self.verification_tracker.get_verification_statistics(days)