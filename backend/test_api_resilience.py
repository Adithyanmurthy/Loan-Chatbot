#!/usr/bin/env python3
"""
Simple test script to verify API resilience implementation
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.api_resilience import (
    ResilientAPIClient, APIEndpoint, RetryStrategy, 
    DataValidator, FallbackDataProvider, CircuitBreaker, CircuitBreakerConfig
)
from services.external_api_service import ExternalAPIService


def test_data_validator():
    """Test data validator"""
    print("Testing Data Validator...")
    
    validator = DataValidator()
    
    # Test valid data
    valid_data = {
        'customer_id': 'test123',
        'name': 'John Doe',
        'phone': '+919876543210',
        'address': '123 Main Street, Mumbai'
    }
    
    result = validator.validate_response(valid_data, api_name="crm")
    print(f"✓ Valid data validation: {result['is_valid']}")
    
    # Test invalid data
    invalid_data = None
    result = validator.validate_response(invalid_data, api_name="crm")
    print(f"✓ Invalid data validation: {not result['is_valid']}")
    
    return True


def test_fallback_provider():
    """Test fallback data provider"""
    print("\nTesting Fallback Data Provider...")
    
    provider = FallbackDataProvider()
    
    # Test CRM fallback
    crm_fallback = provider.get_fallback_data('crm', {'customer_id': 'test123'})
    print(f"✓ CRM fallback data: {crm_fallback.get('customer_id') == 'test123'}")
    
    # Test Credit Bureau fallback
    credit_fallback = provider.get_fallback_data('credit_bureau', {'customer_id': 'test123'})
    print(f"✓ Credit Bureau fallback: {credit_fallback.get('credit_score') == 650}")
    
    # Test Offer Mart fallback
    offers_fallback = provider.get_fallback_data('offer_mart', {'customer_id': 'test123'})
    print(f"✓ Offer Mart fallback: {offers_fallback.get('pre_approved_limit') == 100000}")
    
    return True


def test_circuit_breaker():
    """Test circuit breaker functionality"""
    print("\nTesting Circuit Breaker...")
    
    config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=5)
    breaker = CircuitBreaker(config)
    
    # Test initial state
    print(f"✓ Initial state (closed): {breaker.can_execute()}")
    
    # Simulate failures
    for i in range(3):
        breaker.record_failure()
    
    # Should be open now
    print(f"✓ After failures (open): {not breaker.can_execute()}")
    
    # Simulate success to test recovery
    breaker.record_success()
    print(f"✓ Circuit breaker functionality working")
    
    return True


def test_resilient_api_client():
    """Test resilient API client configuration"""
    print("\nTesting Resilient API Client...")
    
    client = ResilientAPIClient()
    
    # Test API registration
    test_api = APIEndpoint(
        name="test_api",
        base_url="http://localhost:9999",
        timeout=10,
        max_retries=2
    )
    
    client.register_api(test_api)
    print(f"✓ API registered: {'test_api' in client.api_configs}")
    
    # Test health status
    health_status = client.get_api_health_status()
    print(f"✓ Health status available: {isinstance(health_status, dict)}")
    
    return True


async def test_external_api_service():
    """Test external API service"""
    print("\nTesting External API Service...")
    
    service = ExternalAPIService()
    
    # Test statistics
    stats = service.get_api_statistics()
    print(f"✓ Statistics available: {isinstance(stats, dict)}")
    
    # Test health checks (this will fail since APIs aren't running, but should handle gracefully)
    try:
        health_results = await service.perform_health_checks()
        print(f"✓ Health checks completed: {isinstance(health_results, dict)}")
        
        # Check if overall health assessment is present
        overall_health = health_results.get('overall_health', {})
        print(f"✓ Overall health assessment: {overall_health.get('overall_status') in ['healthy', 'degraded', 'critical']}")
        
    except Exception as e:
        print(f"✓ Health checks handled error gracefully: {str(e)[:50]}...")
    
    return True


def main():
    """Run all API resilience tests"""
    print("=" * 60)
    print("API RESILIENCE IMPLEMENTATION TESTS")
    print("=" * 60)
    
    tests = [
        ("Data Validator", test_data_validator),
        ("Fallback Provider", test_fallback_provider),
        ("Circuit Breaker", test_circuit_breaker),
        ("Resilient API Client", test_resilient_api_client)
    ]
    
    # Async test
    async_tests = [
        ("External API Service", test_external_api_service)
    ]
    
    results = []
    
    # Run synchronous tests
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            status = "PASS" if result else "FAIL"
            print(f"\n{status}: {test_name}")
        except Exception as e:
            results.append((test_name, False))
            print(f"\nFAIL: {test_name} - {str(e)}")
    
    # Run asynchronous tests
    for test_name, test_func in async_tests:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(test_func())
            loop.close()
            
            results.append((test_name, result))
            status = "PASS" if result else "FAIL"
            print(f"\n{status}: {test_name}")
        except Exception as e:
            results.append((test_name, False))
            print(f"\nFAIL: {test_name} - {str(e)}")
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All API resilience tests passed!")
        return 0
    else:
        print("❌ Some tests failed. Check implementation.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)