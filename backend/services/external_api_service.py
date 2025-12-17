"""
External API Integration Service
Provides unified interface for all external API calls with resilience and fallback mechanisms
Based on requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from services.api_resilience import resilient_api_client
from services.error_handler import ComprehensiveErrorHandler, ErrorCategory, ErrorContext
from models.customer import CustomerProfile


class APIServiceType(str, Enum):
    """Types of external API services"""
    CRM = "crm"
    CREDIT_BUREAU = "credit_bureau"
    OFFER_MART = "offer_mart"


@dataclass
class APIServiceResult:
    """Result from external API service call"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    source: str = "unknown"  # 'api' or 'fallback'
    api_name: str = ""
    response_time: Optional[float] = None
    fallback_used: bool = False
    validation_warnings: List[str] = None
    
    def __post_init__(self):
        if self.validation_warnings is None:
            self.validation_warnings = []


class ExternalAPIService:
    """
    Unified service for all external API integrations with comprehensive error handling,
    retry logic, and fallback mechanisms.
    """
    
    def __init__(self):
        """Initialize external API service"""
        self.logger = logging.getLogger("external_api_service")
        self.error_handler = ComprehensiveErrorHandler()
        
        # API call statistics
        self.api_stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'fallback_calls': 0,
            'calls_by_api': {}
        }
        
        self.logger.info("External API Service initialized")
    
    async def get_customer_data(self, customer_id: str) -> APIServiceResult:
        """
        Get customer data from CRM API.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            APIServiceResult with customer data
        """
        return await self._make_api_call(
            api_name="crm",
            endpoint=f"/crm/{customer_id}",
            method="GET",
            service_type=APIServiceType.CRM,
            request_params={'customer_id': customer_id}
        )
    
    async def get_credit_score(self, customer_id: str) -> APIServiceResult:
        """
        Get credit score from Credit Bureau API.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            APIServiceResult with credit score data
        """
        return await self._make_api_call(
            api_name="credit_bureau",
            endpoint=f"/credit-score/{customer_id}",
            method="GET",
            service_type=APIServiceType.CREDIT_BUREAU,
            request_params={'customer_id': customer_id}
        )
    
    async def get_pre_approved_offers(self, customer_id: str) -> APIServiceResult:
        """
        Get pre-approved offers from Offer Mart API.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            APIServiceResult with offer data
        """
        return await self._make_api_call(
            api_name="offer_mart",
            endpoint=f"/offers/{customer_id}",
            method="GET",
            service_type=APIServiceType.OFFER_MART,
            request_params={'customer_id': customer_id}
        )
    
    async def _make_api_call(self, api_name: str, endpoint: str, method: str,
                           service_type: APIServiceType, request_params: Dict[str, Any] = None,
                           request_data: Dict[str, Any] = None) -> APIServiceResult:
        """
        Make API call using resilient API client.
        
        Args:
            api_name: Name of the API service
            endpoint: API endpoint path
            method: HTTP method
            service_type: Type of API service
            request_params: Request parameters
            request_data: Request body data
            
        Returns:
            APIServiceResult with response data
        """
        start_time = datetime.now()
        
        try:
            # Update statistics
            self._update_call_stats(api_name, 'attempted')
            
            # Make the API call using resilient client
            api_response = await resilient_api_client.make_request(
                api_name=api_name,
                endpoint=endpoint,
                method=method,
                params=request_params,
                data=request_data
            )
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            if api_response['success']:
                # Successful API call
                result = APIServiceResult(
                    success=True,
                    data=api_response['data'],
                    source=api_response.get('source', 'api'),
                    api_name=api_name,
                    response_time=response_time,
                    fallback_used=api_response.get('source') == 'fallback'
                )
                
                # Validate the response data
                validation_result = self._validate_api_response(service_type, api_response['data'])
                result.validation_warnings = validation_result.get('warnings', [])
                
                if not validation_result['is_valid']:
                    # Data validation failed
                    result.success = False
                    result.error = f"Response validation failed: {'; '.join(validation_result['errors'])}"
                    self._update_call_stats(api_name, 'failed')
                else:
                    self._update_call_stats(api_name, 'successful')
                    if result.fallback_used:
                        self._update_call_stats(api_name, 'fallback')
                
                self.logger.info(f"API call to {api_name} completed: success={result.success}, source={result.source}")
                
                return result
            else:
                # API call failed
                error_message = api_response.get('message', f'{api_name} API call failed')
                
                result = APIServiceResult(
                    success=False,
                    error=error_message,
                    source=api_response.get('source', 'api'),
                    api_name=api_name,
                    response_time=response_time,
                    fallback_used=api_response.get('source') == 'fallback'
                )
                
                self._update_call_stats(api_name, 'failed')
                if result.fallback_used:
                    self._update_call_stats(api_name, 'fallback')
                
                self.logger.error(f"API call to {api_name} failed: {error_message}")
                
                return result
        
        except Exception as e:
            # Handle unexpected errors
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Use error handler
            error_context = ErrorContext(
                additional_data={
                    'api_name': api_name,
                    'endpoint': endpoint,
                    'service_type': service_type.value,
                    'request_params': request_params
                }
            )
            
            error_result = self.error_handler.handle_api_error(api_name, e)
            
            result = APIServiceResult(
                success=False,
                error=error_result.customer_message,
                source='error',
                api_name=api_name,
                response_time=response_time
            )
            
            self._update_call_stats(api_name, 'failed')
            
            self.logger.error(f"Unexpected error in API call to {api_name}: {str(e)}")
            
            return result
    
    def _validate_api_response(self, service_type: APIServiceType, data: Any) -> Dict[str, Any]:
        """
        Validate API response data based on service type.
        
        Args:
            service_type: Type of API service
            data: Response data to validate
            
        Returns:
            Validation result
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            if service_type == APIServiceType.CRM:
                validation_result = self._validate_crm_response(data)
            elif service_type == APIServiceType.CREDIT_BUREAU:
                validation_result = self._validate_credit_bureau_response(data)
            elif service_type == APIServiceType.OFFER_MART:
                validation_result = self._validate_offer_mart_response(data)
            
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    def _validate_crm_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate CRM API response"""
        result = {'is_valid': True, 'errors': [], 'warnings': []}
        
        required_fields = ['customer_id', 'name']
        for field in required_fields:
            if field not in data or not data[field]:
                result['errors'].append(f"Missing required field: {field}")
        
        # Validate phone number if present
        if 'phone' in data:
            phone = str(data['phone'])
            if len(phone) < 10:
                result['warnings'].append("Phone number seems too short")
        
        # Validate address if present
        if 'address' in data:
            address = str(data['address'])
            if len(address) < 10:
                result['warnings'].append("Address seems too short")
        
        if result['errors']:
            result['is_valid'] = False
        
        return result
    
    def _validate_credit_bureau_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Credit Bureau API response"""
        result = {'is_valid': True, 'errors': [], 'warnings': []}
        
        required_fields = ['customer_id', 'credit_score']
        for field in required_fields:
            if field not in data:
                result['errors'].append(f"Missing required field: {field}")
        
        # Validate credit score range
        if 'credit_score' in data:
            try:
                score = int(data['credit_score'])
                if score < 300 or score > 900:
                    result['warnings'].append(f"Credit score {score} is outside typical range (300-900)")
            except (ValueError, TypeError):
                result['errors'].append("Credit score must be a valid number")
        
        if result['errors']:
            result['is_valid'] = False
        
        return result
    
    def _validate_offer_mart_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Offer Mart API response"""
        result = {'is_valid': True, 'errors': [], 'warnings': []}
        
        required_fields = ['customer_id', 'pre_approved_limit']
        for field in required_fields:
            if field not in data:
                result['errors'].append(f"Missing required field: {field}")
        
        # Validate pre-approved limit
        if 'pre_approved_limit' in data:
            try:
                limit = float(data['pre_approved_limit'])
                if limit < 0:
                    result['errors'].append("Pre-approved limit cannot be negative")
                elif limit > 10000000:  # 1 crore
                    result['warnings'].append("Pre-approved limit is unusually high")
            except (ValueError, TypeError):
                result['errors'].append("Pre-approved limit must be a valid number")
        
        # Validate offers array if present
        if 'offers' in data and isinstance(data['offers'], list):
            for i, offer in enumerate(data['offers']):
                if not isinstance(offer, dict):
                    result['warnings'].append(f"Offer {i} is not a valid object")
                    continue
                
                offer_required = ['amount', 'rate', 'tenure']
                for field in offer_required:
                    if field not in offer:
                        result['warnings'].append(f"Offer {i} missing field: {field}")
        
        if result['errors']:
            result['is_valid'] = False
        
        return result
    
    def _update_call_stats(self, api_name: str, call_type: str):
        """Update API call statistics"""
        self.api_stats['total_calls'] += 1
        
        if call_type == 'successful':
            self.api_stats['successful_calls'] += 1
        elif call_type == 'failed':
            self.api_stats['failed_calls'] += 1
        elif call_type == 'fallback':
            self.api_stats['fallback_calls'] += 1
        
        # Update per-API stats
        if api_name not in self.api_stats['calls_by_api']:
            self.api_stats['calls_by_api'][api_name] = {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'fallback': 0
            }
        
        api_stats = self.api_stats['calls_by_api'][api_name]
        if call_type == 'attempted':
            api_stats['total'] += 1
        elif call_type == 'successful':
            api_stats['successful'] += 1
        elif call_type == 'failed':
            api_stats['failed'] += 1
        elif call_type == 'fallback':
            api_stats['fallback'] += 1
    
    def get_comprehensive_customer_data(self, customer_id: str) -> Dict[str, Any]:
        """
        Get comprehensive customer data from all APIs.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            Dictionary containing data from all APIs
        """
        async def fetch_all_data():
            # Make all API calls concurrently
            crm_task = self.get_customer_data(customer_id)
            credit_task = self.get_credit_score(customer_id)
            offers_task = self.get_pre_approved_offers(customer_id)
            
            crm_result, credit_result, offers_result = await asyncio.gather(
                crm_task, credit_task, offers_task, return_exceptions=True
            )
            
            return crm_result, credit_result, offers_result
        
        try:
            # Run the async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            crm_result, credit_result, offers_result = loop.run_until_complete(fetch_all_data())
            
            loop.close()
            
            # Compile comprehensive result
            comprehensive_data = {
                'customer_id': customer_id,
                'timestamp': datetime.now().isoformat(),
                'crm_data': {
                    'success': crm_result.success if isinstance(crm_result, APIServiceResult) else False,
                    'data': crm_result.data if isinstance(crm_result, APIServiceResult) and crm_result.success else None,
                    'error': crm_result.error if isinstance(crm_result, APIServiceResult) else str(crm_result),
                    'source': crm_result.source if isinstance(crm_result, APIServiceResult) else 'error',
                    'fallback_used': crm_result.fallback_used if isinstance(crm_result, APIServiceResult) else False
                },
                'credit_data': {
                    'success': credit_result.success if isinstance(credit_result, APIServiceResult) else False,
                    'data': credit_result.data if isinstance(credit_result, APIServiceResult) and credit_result.success else None,
                    'error': credit_result.error if isinstance(credit_result, APIServiceResult) else str(credit_result),
                    'source': credit_result.source if isinstance(credit_result, APIServiceResult) else 'error',
                    'fallback_used': credit_result.fallback_used if isinstance(credit_result, APIServiceResult) else False
                },
                'offers_data': {
                    'success': offers_result.success if isinstance(offers_result, APIServiceResult) else False,
                    'data': offers_result.data if isinstance(offers_result, APIServiceResult) and offers_result.success else None,
                    'error': offers_result.error if isinstance(offers_result, APIServiceResult) else str(offers_result),
                    'source': offers_result.source if isinstance(offers_result, APIServiceResult) else 'error',
                    'fallback_used': offers_result.fallback_used if isinstance(offers_result, APIServiceResult) else False
                }
            }
            
            # Calculate overall success rate
            successful_apis = sum(1 for api_data in [comprehensive_data['crm_data'], comprehensive_data['credit_data'], comprehensive_data['offers_data']] if api_data['success'])
            comprehensive_data['overall_success_rate'] = successful_apis / 3
            comprehensive_data['all_apis_successful'] = successful_apis == 3
            comprehensive_data['any_fallback_used'] = any(api_data['fallback_used'] for api_data in [comprehensive_data['crm_data'], comprehensive_data['credit_data'], comprehensive_data['offers_data']])
            
            self.logger.info(f"Comprehensive data fetch for {customer_id}: {successful_apis}/3 APIs successful")
            
            return comprehensive_data
            
        except Exception as e:
            self.logger.error(f"Error fetching comprehensive customer data for {customer_id}: {str(e)}")
            return {
                'customer_id': customer_id,
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'overall_success_rate': 0.0,
                'all_apis_successful': False
            }
    
    def get_api_statistics(self) -> Dict[str, Any]:
        """
        Get API call statistics.
        
        Returns:
            Dictionary containing API statistics
        """
        stats = self.api_stats.copy()
        
        # Calculate success rate
        if stats['total_calls'] > 0:
            stats['success_rate'] = stats['successful_calls'] / stats['total_calls']
            stats['failure_rate'] = stats['failed_calls'] / stats['total_calls']
            stats['fallback_rate'] = stats['fallback_calls'] / stats['total_calls']
        else:
            stats['success_rate'] = 0.0
            stats['failure_rate'] = 0.0
            stats['fallback_rate'] = 0.0
        
        # Add resilient API client health status
        try:
            stats['api_health_status'] = resilient_api_client.get_api_health_status()
        except Exception as e:
            stats['api_health_error'] = str(e)
        
        return stats
    
    async def perform_health_checks(self) -> Dict[str, Any]:
        """
        Perform health checks on all registered APIs.
        
        Returns:
            Dictionary containing health check results
        """
        health_results = {}
        
        api_names = ['crm', 'credit_bureau', 'offer_mart']
        
        for api_name in api_names:
            try:
                is_healthy = await resilient_api_client.health_check(api_name)
                health_results[api_name] = {
                    'healthy': is_healthy,
                    'checked_at': datetime.now().isoformat()
                }
            except Exception as e:
                health_results[api_name] = {
                    'healthy': False,
                    'error': str(e),
                    'checked_at': datetime.now().isoformat()
                }
        
        # Overall health assessment
        healthy_apis = sum(1 for result in health_results.values() if result.get('healthy', False))
        health_results['overall_health'] = {
            'healthy_apis': healthy_apis,
            'total_apis': len(api_names),
            'health_percentage': (healthy_apis / len(api_names)) * 100,
            'overall_status': 'healthy' if healthy_apis == len(api_names) else 'degraded' if healthy_apis > 0 else 'critical'
        }
        
        return health_results


# Global external API service instance
external_api_service = ExternalAPIService()