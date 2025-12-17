"""
API Resilience and Retry Logic Service
Implements exponential backoff retry, fallback mechanisms, and data validation for external APIs
Based on requirements: 8.4, 8.5
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, Optional, List, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from services.error_handler import (
    ComprehensiveErrorHandler, ErrorCategory, ErrorContext, 
    ErrorHandlingResult
)


class APIStatus(str, Enum):
    """API service status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    MAINTENANCE = "maintenance"


class RetryStrategy(str, Enum):
    """Retry strategy types"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_INTERVAL = "fixed_interval"
    IMMEDIATE = "immediate"


@dataclass
class APIEndpoint:
    """Configuration for an API endpoint"""
    name: str
    base_url: str
    timeout: int = 30
    max_retries: int = 3
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    fallback_enabled: bool = True
    circuit_breaker_enabled: bool = True
    health_check_endpoint: Optional[str] = None
    required_headers: Dict[str, str] = field(default_factory=dict)
    validation_schema: Optional[Dict[str, Any]] = None


@dataclass
class RetryConfig:
    """Retry configuration"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    backoff_factor: float = 0.3
    status_forcelist: List[int] = field(default_factory=lambda: [500, 502, 503, 504, 429])


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    expected_exception: type = Exception


class CircuitBreakerState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    """Circuit breaker implementation"""
    config: CircuitBreakerConfig
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    success_count: int = 0
    
    def can_execute(self) -> bool:
        """Check if request can be executed"""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if self.last_failure_time:
                time_since_failure = datetime.now() - self.last_failure_time
                if time_since_failure.total_seconds() >= self.config.recovery_timeout:
                    self.state = CircuitBreakerState.HALF_OPEN
                    return True
            return False
        elif self.state == CircuitBreakerState.HALF_OPEN:
            return True
        return False
    
    def record_success(self):
        """Record successful execution"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 3:  # Require 3 successes to close
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = max(0, self.failure_count - 1)
    
    def record_failure(self):
        """Record failed execution"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        self.success_count = 0
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN


class DataValidator:
    """Validates and sanitizes external API data"""
    
    def __init__(self):
        """Initialize data validator"""
        self.logger = logging.getLogger("api_resilience.data_validator")
    
    def validate_response(self, data: Any, schema: Optional[Dict[str, Any]] = None,
                         api_name: str = "unknown") -> Dict[str, Any]:
        """
        Validate API response data.
        
        Args:
            data: Response data to validate
            schema: Optional validation schema
            api_name: Name of the API for logging
            
        Returns:
            Validation result
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'sanitized_data': data
        }
        
        try:
            # Basic validation
            if data is None:
                validation_result['is_valid'] = False
                validation_result['errors'].append("Response data is None")
                return validation_result
            
            # Type validation
            if not isinstance(data, (dict, list)):
                validation_result['warnings'].append(f"Unexpected data type: {type(data)}")
            
            # Schema validation if provided
            if schema:
                schema_validation = self._validate_against_schema(data, schema)
                validation_result['errors'].extend(schema_validation['errors'])
                validation_result['warnings'].extend(schema_validation['warnings'])
                if schema_validation['errors']:
                    validation_result['is_valid'] = False
            
            # Sanitize data
            validation_result['sanitized_data'] = self._sanitize_data(data)
            
            self.logger.info(f"Validated response from {api_name}: {'valid' if validation_result['is_valid'] else 'invalid'}")
            
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Validation error: {str(e)}")
            self.logger.error(f"Error validating response from {api_name}: {str(e)}")
        
        return validation_result
    
    def _validate_against_schema(self, data: Any, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against schema"""
        result = {'errors': [], 'warnings': []}
        
        try:
            # Simple schema validation (can be extended with jsonschema library)
            if isinstance(data, dict) and isinstance(schema, dict):
                required_fields = schema.get('required', [])
                for field in required_fields:
                    if field not in data:
                        result['errors'].append(f"Missing required field: {field}")
                
                # Type checking
                field_types = schema.get('properties', {})
                for field, expected_type in field_types.items():
                    if field in data:
                        actual_type = type(data[field]).__name__
                        if actual_type != expected_type:
                            result['warnings'].append(f"Field {field} type mismatch: expected {expected_type}, got {actual_type}")
        
        except Exception as e:
            result['errors'].append(f"Schema validation error: {str(e)}")
        
        return result
    
    def _sanitize_data(self, data: Any) -> Any:
        """Sanitize data by removing potentially harmful content"""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                # Sanitize key and value
                clean_key = self._sanitize_string(str(key))
                clean_value = self._sanitize_data(value)
                sanitized[clean_key] = clean_value
            return sanitized
        
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        
        elif isinstance(data, str):
            return self._sanitize_string(data)
        
        else:
            return data
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitize string data"""
        if not isinstance(text, str):
            return text
        
        # Remove potentially harmful characters
        # This is a basic implementation - can be enhanced based on security requirements
        sanitized = text.replace('<script>', '').replace('</script>', '')
        sanitized = sanitized.replace('javascript:', '')
        sanitized = sanitized.replace('data:', '')
        
        return sanitized.strip()


class FallbackDataProvider:
    """Provides fallback data when APIs are unavailable"""
    
    def __init__(self):
        """Initialize fallback data provider"""
        self.logger = logging.getLogger("api_resilience.fallback_provider")
        
        # Default fallback data for different APIs
        self.fallback_data = {
            'crm': {
                'default_customer': {
                    'id': 'fallback_customer',
                    'name': 'Valued Customer',
                    'phone': 'Not Available',
                    'address': 'Not Available',
                    'kyc_status': 'pending_verification'
                }
            },
            'credit_bureau': {
                'default_score': {
                    'credit_score': 650,  # Conservative default
                    'score_date': datetime.now().isoformat(),
                    'bureau_name': 'fallback_data',
                    'status': 'estimated'
                }
            },
            'offer_mart': {
                'default_offers': {
                    'pre_approved_limit': 100000,  # Conservative default
                    'interest_rate': 18.0,  # Higher default rate
                    'offers': [
                        {
                            'amount': 50000,
                            'rate': 18.0,
                            'tenure': 24
                        }
                    ]
                }
            }
        }
    
    def get_fallback_data(self, api_name: str, request_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get fallback data for API.
        
        Args:
            api_name: Name of the API
            request_params: Original request parameters
            
        Returns:
            Fallback data
        """
        try:
            api_fallback = self.fallback_data.get(api_name.lower(), {})
            
            if api_name.lower() == 'crm':
                return self._get_crm_fallback(request_params)
            elif api_name.lower() == 'credit_bureau':
                return self._get_credit_bureau_fallback(request_params)
            elif api_name.lower() == 'offer_mart':
                return self._get_offer_mart_fallback(request_params)
            else:
                return api_fallback
        
        except Exception as e:
            self.logger.error(f"Error generating fallback data for {api_name}: {str(e)}")
            return {'error': 'fallback_data_unavailable', 'message': 'Unable to provide fallback data'}
    
    def _get_crm_fallback(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get CRM fallback data"""
        customer_id = params.get('customer_id', 'unknown') if params else 'unknown'
        
        return {
            'customer_id': customer_id,
            'name': 'Valued Customer',
            'phone': 'Please provide your phone number',
            'address': 'Please provide your address',
            'kyc_status': 'manual_verification_required',
            'data_source': 'fallback',
            'requires_manual_verification': True
        }
    
    def _get_credit_bureau_fallback(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get credit bureau fallback data"""
        customer_id = params.get('customer_id', 'unknown') if params else 'unknown'
        
        return {
            'customer_id': customer_id,
            'credit_score': 650,  # Conservative score
            'score_date': datetime.now().isoformat(),
            'bureau_name': 'fallback_estimation',
            'status': 'estimated_score',
            'data_source': 'fallback',
            'requires_verification': True,
            'note': 'This is an estimated score. Actual verification required.'
        }
    
    def _get_offer_mart_fallback(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get offer mart fallback data"""
        customer_id = params.get('customer_id', 'unknown') if params else 'unknown'
        
        return {
            'customer_id': customer_id,
            'pre_approved_limit': 100000,  # Conservative limit
            'interest_rate': 18.0,  # Higher default rate
            'offers': [
                {
                    'amount': 50000,
                    'rate': 18.0,
                    'tenure': 24,
                    'type': 'conservative_offer'
                },
                {
                    'amount': 75000,
                    'rate': 19.0,
                    'tenure': 36,
                    'type': 'standard_offer'
                }
            ],
            'data_source': 'fallback',
            'note': 'These are conservative offers. Better rates may be available upon verification.'
        }


class ResilientAPIClient:
    """Resilient API client with retry logic, circuit breaker, and fallback mechanisms"""
    
    def __init__(self):
        """Initialize resilient API client"""
        self.logger = logging.getLogger("api_resilience.client")
        self.error_handler = ComprehensiveErrorHandler()
        self.data_validator = DataValidator()
        self.fallback_provider = FallbackDataProvider()
        
        # API configurations
        self.api_configs: Dict[str, APIEndpoint] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.api_health_status: Dict[str, APIStatus] = {}
        
        # Session with retry configuration
        self.session = self._create_session()
        
        # Initialize default API configurations
        self._initialize_default_configs()
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry configuration"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],  # Updated parameter name
            backoff_factor=0.3
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _initialize_default_configs(self):
        """Initialize default API configurations"""
        # CRM API configuration
        self.register_api(APIEndpoint(
            name="crm",
            base_url="http://localhost:3001",
            timeout=30,
            max_retries=3,
            retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            health_check_endpoint="/health",
            validation_schema={
                'required': ['customer_id', 'name'],
                'properties': {
                    'customer_id': 'str',
                    'name': 'str',
                    'phone': 'str',
                    'address': 'str'
                }
            }
        ))
        
        # Credit Bureau API configuration
        self.register_api(APIEndpoint(
            name="credit_bureau",
            base_url="http://localhost:3002",
            timeout=45,
            max_retries=3,
            retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            health_check_endpoint="/health",
            validation_schema={
                'required': ['customer_id', 'credit_score'],
                'properties': {
                    'customer_id': 'str',
                    'credit_score': 'int'
                }
            }
        ))
        
        # Offer Mart API configuration
        self.register_api(APIEndpoint(
            name="offer_mart",
            base_url="http://localhost:3003",
            timeout=30,
            max_retries=3,
            retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            health_check_endpoint="/health",
            validation_schema={
                'required': ['customer_id', 'pre_approved_limit'],
                'properties': {
                    'customer_id': 'str',
                    'pre_approved_limit': 'int'
                }
            }
        ))
    
    def register_api(self, api_config: APIEndpoint):
        """
        Register an API endpoint configuration.
        
        Args:
            api_config: API endpoint configuration
        """
        self.api_configs[api_config.name] = api_config
        
        # Initialize circuit breaker
        if api_config.circuit_breaker_enabled:
            self.circuit_breakers[api_config.name] = CircuitBreaker(
                config=CircuitBreakerConfig(
                    failure_threshold=5,
                    recovery_timeout=60
                )
            )
        
        # Initialize health status
        self.api_health_status[api_config.name] = APIStatus.HEALTHY
        
        self.logger.info(f"Registered API: {api_config.name}")
    
    async def make_request(self, api_name: str, endpoint: str, method: str = "GET",
                          params: Dict[str, Any] = None, data: Dict[str, Any] = None,
                          headers: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Make resilient API request with retry logic and fallback.
        
        Args:
            api_name: Name of the API
            endpoint: API endpoint path
            method: HTTP method
            params: Query parameters
            data: Request body data
            headers: Request headers
            
        Returns:
            API response or fallback data
        """
        api_config = self.api_configs.get(api_name)
        if not api_config:
            raise ValueError(f"API {api_name} not registered")
        
        # Check circuit breaker
        circuit_breaker = self.circuit_breakers.get(api_name)
        if circuit_breaker and not circuit_breaker.can_execute():
            self.logger.warning(f"Circuit breaker open for {api_name}, using fallback")
            return self._handle_fallback(api_name, params or data or {})
        
        # Prepare request
        url = f"{api_config.base_url}{endpoint}"
        request_headers = {**api_config.required_headers, **(headers or {})}
        
        # Execute request with retry logic
        for attempt in range(api_config.max_retries + 1):
            try:
                # Calculate delay for retry
                if attempt > 0:
                    delay = self._calculate_retry_delay(attempt, api_config.retry_strategy)
                    await asyncio.sleep(delay)
                
                self.logger.info(f"Making request to {api_name} (attempt {attempt + 1})")
                
                # Make the request
                response = await self._execute_request(
                    method, url, params, data, request_headers, api_config.timeout
                )
                
                # Validate response
                validation_result = self.data_validator.validate_response(
                    response, api_config.validation_schema, api_name
                )
                
                if validation_result['is_valid']:
                    # Success - record in circuit breaker
                    if circuit_breaker:
                        circuit_breaker.record_success()
                    
                    self.api_health_status[api_name] = APIStatus.HEALTHY
                    
                    return {
                        'success': True,
                        'data': validation_result['sanitized_data'],
                        'source': 'api',
                        'api_name': api_name,
                        'attempt': attempt + 1
                    }
                else:
                    # Validation failed
                    raise ValueError(f"Response validation failed: {validation_result['errors']}")
            
            except Exception as e:
                # Record failure in circuit breaker
                if circuit_breaker:
                    circuit_breaker.record_failure()
                
                self.api_health_status[api_name] = APIStatus.DEGRADED
                
                # Handle error
                error_context = ErrorContext(
                    additional_data={
                        'api_name': api_name,
                        'endpoint': endpoint,
                        'attempt': attempt + 1,
                        'max_attempts': api_config.max_retries + 1
                    }
                )
                
                error_result = self.error_handler.handle_api_error(api_name, e)
                
                self.logger.error(f"API request failed (attempt {attempt + 1}): {str(e)}")
                
                # If this is the last attempt, use fallback
                if attempt >= api_config.max_retries:
                    if api_config.fallback_enabled:
                        self.logger.info(f"Using fallback for {api_name} after {attempt + 1} attempts")
                        return self._handle_fallback(api_name, params or data or {})
                    else:
                        raise Exception(f"API {api_name} failed after {attempt + 1} attempts: {error_result.customer_message}")
        
        # This should never be reached
        raise Exception(f"Unexpected error in API request to {api_name}")
    
    async def _execute_request(self, method: str, url: str, params: Dict[str, Any] = None,
                              data: Dict[str, Any] = None, headers: Dict[str, str] = None,
                              timeout: int = 30) -> Any:
        """Execute HTTP request"""
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params, headers=headers, timeout=timeout)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, headers=headers, timeout=timeout)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, headers=headers, timeout=timeout)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            # Try to parse JSON response
            try:
                return response.json()
            except json.JSONDecodeError:
                return {'raw_response': response.text}
        
        except requests.exceptions.Timeout:
            raise Exception(f"Request timeout after {timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise Exception("Connection error - API may be unavailable")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Request execution error: {str(e)}")
    
    def _calculate_retry_delay(self, attempt: int, strategy: RetryStrategy) -> float:
        """Calculate delay before retry based on strategy"""
        if strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = min(2 ** attempt, 60)  # Cap at 60 seconds
        elif strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = min(attempt * 2, 30)  # Cap at 30 seconds
        elif strategy == RetryStrategy.FIXED_INTERVAL:
            delay = 5  # Fixed 5 second delay
        else:  # IMMEDIATE
            delay = 0
        
        # Add jitter to prevent thundering herd
        import random
        jitter = random.uniform(0.1, 0.5)
        return delay + jitter
    
    def _handle_fallback(self, api_name: str, request_params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle fallback when API is unavailable"""
        try:
            fallback_data = self.fallback_provider.get_fallback_data(api_name, request_params)
            
            self.api_health_status[api_name] = APIStatus.UNAVAILABLE
            
            return {
                'success': True,
                'data': fallback_data,
                'source': 'fallback',
                'api_name': api_name,
                'note': 'This data is from fallback source due to API unavailability'
            }
        
        except Exception as e:
            self.logger.error(f"Fallback failed for {api_name}: {str(e)}")
            return {
                'success': False,
                'error': 'fallback_failed',
                'message': f"Both API and fallback failed for {api_name}",
                'api_name': api_name
            }
    
    def get_api_health_status(self) -> Dict[str, Any]:
        """
        Get health status of all registered APIs.
        
        Returns:
            Dictionary containing API health information
        """
        health_info = {}
        
        for api_name, status in self.api_health_status.items():
            circuit_breaker = self.circuit_breakers.get(api_name)
            
            health_info[api_name] = {
                'status': status.value,
                'circuit_breaker_state': circuit_breaker.state.value if circuit_breaker else 'disabled',
                'failure_count': circuit_breaker.failure_count if circuit_breaker else 0,
                'last_failure': circuit_breaker.last_failure_time.isoformat() if circuit_breaker and circuit_breaker.last_failure_time else None
            }
        
        return health_info
    
    async def health_check(self, api_name: str) -> bool:
        """
        Perform health check on specific API.
        
        Args:
            api_name: Name of the API to check
            
        Returns:
            True if API is healthy, False otherwise
        """
        api_config = self.api_configs.get(api_name)
        if not api_config or not api_config.health_check_endpoint:
            return False
        
        try:
            url = f"{api_config.base_url}{api_config.health_check_endpoint}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                self.api_health_status[api_name] = APIStatus.HEALTHY
                return True
            else:
                self.api_health_status[api_name] = APIStatus.DEGRADED
                return False
        
        except Exception as e:
            self.logger.error(f"Health check failed for {api_name}: {str(e)}")
            self.api_health_status[api_name] = APIStatus.UNAVAILABLE
            return False


# Global resilient API client instance
resilient_api_client = ResilientAPIClient()