"""
CRM API Client with retry logic and data validation
Implements robust integration with CRM server for customer data retrieval
Based on requirements: 3.1, 3.5, 8.1
"""

import asyncio
import logging
import requests
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
from dataclasses import dataclass
from enum import Enum

from models.customer import CustomerProfile
from services.api_resilience import resilient_api_client


class CRMErrorType(str, Enum):
    """Enumeration for CRM error types"""
    TIMEOUT = "timeout"
    SERVER_ERROR = "server_error"
    NOT_FOUND = "not_found"
    NETWORK_ERROR = "network_error"
    INVALID_RESPONSE = "invalid_response"
    AUTHENTICATION_ERROR = "authentication_error"


@dataclass
class CRMResponse:
    """Data class for CRM API responses"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_type: Optional[CRMErrorType] = None
    response_time: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class CRMDataValidator:
    """Validator for CRM data integrity and completeness"""
    
    REQUIRED_FIELDS = ['id', 'name', 'phone', 'address']
    OPTIONAL_FIELDS = ['age', 'city', 'employmentType', 'company', 'salary', 'kycStatus', 'lastUpdated']
    
    @classmethod
    def validate_customer_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate customer data from CRM response.
        
        Args:
            data: Raw customer data from CRM
            
        Returns:
            Validation result with status and issues
        """
        validation_result = {
            'valid': True,
            'issues': [],
            'warnings': [],
            'sanitized_data': {}
        }
        
        # Check required fields
        missing_fields = []
        for field in cls.REQUIRED_FIELDS:
            if field not in data or not data[field]:
                missing_fields.append(field)
        
        if missing_fields:
            validation_result['valid'] = False
            validation_result['issues'].append(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Sanitize and validate individual fields
        sanitized_data = {}
        
        # Validate and sanitize name
        if 'name' in data:
            name = str(data['name']).strip()
            if len(name) < 2:
                validation_result['issues'].append("Name too short")
            elif len(name) > 100:
                validation_result['warnings'].append("Name unusually long")
            sanitized_data['name'] = name
        
        # Validate and sanitize phone
        if 'phone' in data:
            phone = cls._sanitize_phone_number(data['phone'])
            if not cls._is_valid_phone_number(phone):
                validation_result['issues'].append("Invalid phone number format")
            sanitized_data['phone'] = phone
        
        # Validate and sanitize address
        if 'address' in data:
            address = str(data['address']).strip()
            if len(address) < 10:
                validation_result['issues'].append("Address too short")
            elif len(address) > 500:
                validation_result['warnings'].append("Address unusually long")
            sanitized_data['address'] = address
        
        # Validate age if present
        if 'age' in data:
            try:
                age = int(data['age'])
                if age < 18 or age > 100:
                    validation_result['issues'].append("Age out of valid range (18-100)")
                sanitized_data['age'] = age
            except (ValueError, TypeError):
                validation_result['warnings'].append("Invalid age format")
        
        # Validate salary if present
        if 'salary' in data:
            try:
                salary = float(data['salary'])
                if salary < 0:
                    validation_result['issues'].append("Salary cannot be negative")
                elif salary > 10000000:  # 1 crore
                    validation_result['warnings'].append("Salary unusually high")
                sanitized_data['salary'] = salary
            except (ValueError, TypeError):
                validation_result['warnings'].append("Invalid salary format")
        
        # Copy other valid fields
        for field in cls.OPTIONAL_FIELDS:
            if field in data and field not in sanitized_data:
                sanitized_data[field] = data[field]
        
        # Copy required fields that passed validation
        for field in cls.REQUIRED_FIELDS:
            if field in data and field not in sanitized_data:
                sanitized_data[field] = data[field]
        
        validation_result['sanitized_data'] = sanitized_data
        
        # Mark as invalid if there are critical issues
        if validation_result['issues']:
            validation_result['valid'] = False
        
        return validation_result
    
    @staticmethod
    def _sanitize_phone_number(phone: Any) -> str:
        """Sanitize phone number by removing non-digit characters"""
        if not phone:
            return ""
        
        phone_str = str(phone)
        # Remove all non-digit characters except +
        sanitized = ''.join(c for c in phone_str if c.isdigit() or c == '+')
        
        # Handle Indian phone number formats
        if sanitized.startswith('+91'):
            return sanitized
        elif sanitized.startswith('91') and len(sanitized) == 12:
            return '+' + sanitized
        elif sanitized.startswith('0') and len(sanitized) == 11:
            return '+91' + sanitized[1:]
        elif len(sanitized) == 10:
            return '+91' + sanitized
        
        return sanitized
    
    @staticmethod
    def _is_valid_phone_number(phone: str) -> bool:
        """Validate Indian phone number format"""
        if not phone:
            return False
        
        # Remove +91 prefix for validation
        if phone.startswith('+91'):
            digits = phone[3:]
        else:
            digits = phone
        
        # Check if it's 10 digits and starts with valid prefix
        if len(digits) == 10 and digits.isdigit():
            return digits[0] in '6789'  # Valid Indian mobile prefixes
        
        return False


class CRMClient:
    """
    CRM API Client with comprehensive retry logic, error handling, and data validation.
    Provides robust integration with CRM server for customer data operations.
    """
    
    def __init__(self, base_url: str = "http://localhost:3001", timeout: int = 30):
        """
        Initialize CRM client.
        
        Args:
            base_url: Base URL for CRM API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        
        # Retry configuration
        self.max_retries = 3
        self.base_retry_delay = 1  # seconds
        self.max_retry_delay = 16  # seconds
        self.backoff_multiplier = 2
        
        # Circuit breaker configuration
        self.failure_threshold = 5
        self.recovery_timeout = 60  # seconds
        self.failure_count = 0
        self.last_failure_time = None
        self.circuit_open = False
        
        # Request tracking
        self.request_history: List[CRMResponse] = []
        self.max_history_size = 100
        
        # Setup logging
        self.logger = logging.getLogger(f"crm_client")
        self.logger.setLevel(logging.INFO)
        
        self.logger.info(f"CRM Client initialized with base URL: {self.base_url}")
    
    def get_customer_data(self, customer_id: str) -> CRMResponse:
        """
        Retrieve customer data from CRM with retry logic and validation.
        
        Args:
            customer_id: Unique customer identifier
            
        Returns:
            CRMResponse containing customer data or error information
        """
        if not customer_id:
            return CRMResponse(
                success=False,
                error="Customer ID is required",
                error_type=CRMErrorType.INVALID_RESPONSE
            )
        
        self.logger.info(f"Fetching customer data for ID: {customer_id}")
        
        try:
            # Use resilient API client for the request
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            start_time = time.time()
            api_response = loop.run_until_complete(
                resilient_api_client.make_request(
                    api_name="crm",
                    endpoint=f"/crm/{customer_id}",
                    method="GET"
                )
            )
            response_time = time.time() - start_time
            
            loop.close()
            
            if api_response['success']:
                # Validate and sanitize the data
                customer_data = api_response['data']
                validation_result = CRMDataValidator.validate_customer_data(customer_data)
                
                if validation_result['valid']:
                    crm_response = CRMResponse(
                        success=True,
                        data=validation_result['sanitized_data'],
                        response_time=response_time
                    )
                    
                    self._record_success()
                    self._add_to_history(crm_response)
                    
                    self.logger.info(f"Successfully retrieved and validated data for customer {customer_id}")
                    
                    if validation_result['warnings']:
                        self.logger.warning(f"Data validation warnings for {customer_id}: {validation_result['warnings']}")
                    
                    return crm_response
                else:
                    # Data validation failed
                    error_msg = f"Data validation failed: {'; '.join(validation_result['issues'])}"
                    crm_response = CRMResponse(
                        success=False,
                        error=error_msg,
                        error_type=CRMErrorType.INVALID_RESPONSE,
                        response_time=response_time
                    )
                    
                    self._record_failure()
                    self._add_to_history(crm_response)
                    
                    self.logger.error(f"Data validation failed for customer {customer_id}: {error_msg}")
                    return crm_response
            else:
                # API request failed - determine error type
                error_msg = api_response.get('message', 'CRM API request failed')
                
                # Map API errors to CRM error types
                if 'timeout' in error_msg.lower():
                    error_type = CRMErrorType.TIMEOUT
                elif 'not found' in error_msg.lower() or '404' in error_msg:
                    error_type = CRMErrorType.NOT_FOUND
                elif 'connection' in error_msg.lower() or 'network' in error_msg.lower():
                    error_type = CRMErrorType.NETWORK_ERROR
                elif 'server' in error_msg.lower() or '5' in error_msg[:1]:
                    error_type = CRMErrorType.SERVER_ERROR
                else:
                    error_type = CRMErrorType.SERVER_ERROR
                
                crm_response = CRMResponse(
                    success=False,
                    error=error_msg,
                    error_type=error_type,
                    response_time=response_time
                )
                
                # Don't record 404 as failure for circuit breaker
                if error_type != CRMErrorType.NOT_FOUND:
                    self._record_failure()
                
                self._add_to_history(crm_response)
                
                if error_type == CRMErrorType.NOT_FOUND:
                    self.logger.warning(f"Customer {customer_id} not found in CRM")
                else:
                    self.logger.error(f"CRM API request failed for customer {customer_id}: {error_msg}")
                
                return crm_response
                
        except Exception as e:
            error_msg = f"CRM client error: {str(e)}"
            crm_response = CRMResponse(
                success=False,
                error=error_msg,
                error_type=CRMErrorType.SERVER_ERROR,
                response_time=time.time() - start_time if 'start_time' in locals() else None
            )
            
            self._record_failure()
            self._add_to_history(crm_response)
            
            self.logger.error(f"CRM client error for customer {customer_id}: {error_msg}")
            return crm_response
    
    def validate_customer_exists(self, customer_id: str) -> bool:
        """
        Check if a customer exists in CRM without retrieving full data.
        
        Args:
            customer_id: Customer identifier to check
            
        Returns:
            True if customer exists, False otherwise
        """
        response = self.get_customer_data(customer_id)
        return response.success
    
    def get_customer_profile(self, customer_id: str) -> Optional[CustomerProfile]:
        """
        Get customer data as a CustomerProfile object.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            CustomerProfile object or None if not found/invalid
        """
        response = self.get_customer_data(customer_id)
        
        if not response.success or not response.data:
            return None
        
        try:
            # Map CRM data to CustomerProfile format
            crm_data = response.data
            
            profile_data = {
                'id': crm_data['id'],
                'name': crm_data['name'],
                'phone': crm_data['phone'],
                'address': crm_data['address'],
                'age': crm_data.get('age', 25),  # Default age if not provided
                'city': crm_data.get('city', 'Unknown'),
                'current_loans': [],  # CRM doesn't provide loan data in this mock
                'credit_score': 750,  # Default, will be fetched from credit bureau
                'pre_approved_limit': 0,  # Will be fetched from offer mart
                'salary': crm_data.get('salary'),
                'employment_type': crm_data.get('employmentType', 'salaried')
            }
            
            return CustomerProfile(**profile_data)
            
        except Exception as e:
            self.logger.error(f"Failed to create CustomerProfile for {customer_id}: {str(e)}")
            return None
    
    def _is_circuit_open(self) -> bool:
        """Check if circuit breaker is open"""
        if not self.circuit_open:
            return False
        
        # Check if recovery timeout has passed
        if self.last_failure_time and \
           datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout):
            self.circuit_open = False
            self.failure_count = 0
            self.logger.info("Circuit breaker closed - attempting recovery")
            return False
        
        return True
    
    def _record_success(self):
        """Record a successful request"""
        self.failure_count = 0
        self.circuit_open = False
    
    def _record_failure(self):
        """Record a failed request and update circuit breaker state"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.circuit_open = True
            self.logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def _add_to_history(self, response: CRMResponse):
        """Add response to request history"""
        self.request_history.append(response)
        
        # Maintain history size limit
        if len(self.request_history) > self.max_history_size:
            self.request_history = self.request_history[-self.max_history_size:]
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of CRM client.
        
        Returns:
            Dictionary containing health metrics
        """
        recent_requests = [r for r in self.request_history 
                          if r.timestamp > datetime.now() - timedelta(minutes=5)]
        
        success_count = sum(1 for r in recent_requests if r.success)
        total_count = len(recent_requests)
        
        avg_response_time = None
        if recent_requests:
            response_times = [r.response_time for r in recent_requests if r.response_time]
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
        
        return {
            "circuit_open": self.circuit_open,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "recent_success_rate": success_count / total_count if total_count > 0 else None,
            "recent_request_count": total_count,
            "average_response_time": avg_response_time,
            "base_url": self.base_url
        }
    
    def reset_circuit_breaker(self):
        """Manually reset circuit breaker"""
        self.circuit_open = False
        self.failure_count = 0
        self.last_failure_time = None
        self.logger.info("Circuit breaker manually reset")
    
    def get_api_resilience_status(self) -> Dict[str, Any]:
        """
        Get status from the resilient API client.
        
        Returns:
            Dictionary containing API resilience status
        """
        try:
            api_health = resilient_api_client.get_api_health_status()
            crm_health = api_health.get('crm', {})
            
            return {
                'resilient_api_status': crm_health,
                'local_circuit_breaker': {
                    'circuit_open': self.circuit_open,
                    'failure_count': self.failure_count,
                    'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None
                },
                'integration_status': 'enhanced_with_resilient_client'
            }
        except Exception as e:
            self.logger.error(f"Error getting API resilience status: {str(e)}")
            return {
                'error': str(e),
                'integration_status': 'error_getting_status'
            }