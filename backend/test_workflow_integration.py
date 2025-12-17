#!/usr/bin/env python3
"""
Workflow Integration Test
Tests a complete customer journey through the system
"""

import requests
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_complete_workflow():
    """Test a complete customer workflow"""
    base_url = "http://localhost:5000"
    session_id = None
    
    try:
        # Step 1: Initiate conversation
        logger.info("Step 1: Initiating conversation...")
        response = requests.post(f"{base_url}/api/chat/message", 
                               json={'message': 'Hello', 'customer_id': 'CUST001'}, 
                               timeout=30)
        assert response.status_code == 200, f"Failed to initiate: {response.status_code}"
        
        data = response.json()
        session_id = data.get('session_id')
        logger.info(f"✓ Conversation initiated. Session: {session_id}")
        logger.info(f"Greeting: {data.get('greeting', 'N/A')}")
        
        # Step 2: Express loan interest
        logger.info("Step 2: Expressing loan interest...")
        response = requests.post(f"{base_url}/api/chat/message", 
                               json={
                                   'message': 'I want a personal loan of ₹300000',
                                   'session_id': session_id
                               }, timeout=30)
        assert response.status_code == 200, f"Failed to send message: {response.status_code}"
        
        data = response.json()
        logger.info(f"✓ Loan interest expressed")
        logger.info(f"Response: {data.get('response', 'N/A')[:100]}...")
        
        # Step 3: Provide customer information
        logger.info("Step 3: Providing customer information...")
        response = requests.post(f"{base_url}/api/chat/message", 
                               json={
                                   'message': 'My name is Rajesh Kumar, I am 32 years old from Mumbai',
                                   'session_id': session_id
                               }, timeout=30)
        assert response.status_code == 200, f"Failed to send message: {response.status_code}"
        
        data = response.json()
        logger.info(f"✓ Customer information provided")
        logger.info(f"Response: {data.get('response', 'N/A')[:100]}...")
        
        # Step 4: Agree to terms
        logger.info("Step 4: Agreeing to terms...")
        response = requests.post(f"{base_url}/api/chat/message", 
                               json={
                                   'message': 'Yes, I agree to the loan terms',
                                   'session_id': session_id
                               }, timeout=30)
        assert response.status_code == 200, f"Failed to send message: {response.status_code}"
        
        data = response.json()
        logger.info(f"✓ Terms agreed")
        logger.info(f"Response: {data.get('response', 'N/A')[:100]}...")
        
        # Step 5: Proceed with verification
        logger.info("Step 5: Proceeding with verification...")
        response = requests.post(f"{base_url}/api/chat/message", 
                               json={
                                   'message': 'Please proceed with verification',
                                   'session_id': session_id
                               }, timeout=30)
        assert response.status_code == 200, f"Failed to send message: {response.status_code}"
        
        data = response.json()
        logger.info(f"✓ Verification initiated")
        logger.info(f"Response: {data.get('response', 'N/A')[:100]}...")
        
        # Step 6: Check eligibility
        logger.info("Step 6: Checking eligibility...")
        response = requests.post(f"{base_url}/api/chat/message", 
                               json={
                                   'message': 'Please check my loan eligibility',
                                   'session_id': session_id
                               }, timeout=30)
        assert response.status_code == 200, f"Failed to send message: {response.status_code}"
        
        data = response.json()
        logger.info(f"✓ Eligibility check completed")
        logger.info(f"Response: {data.get('response', 'N/A')[:100]}...")
        
        # Check final status
        logger.info("Checking final conversation status...")
        response = requests.get(f"{base_url}/api/chat/status", 
                              params={'session_id': session_id}, timeout=10)
        assert response.status_code == 200, f"Failed to get status: {response.status_code}"
        
        status_data = response.json()
        logger.info(f"Final conversation stage: {status_data.get('conversation_stage')}")
        logger.info(f"Current agent: {status_data.get('current_agent')}")
        
        logger.info("✅ Complete workflow test PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Workflow test FAILED: {e}")
        return False
    
    finally:
        # Cleanup
        if session_id:
            try:
                requests.post(f"{base_url}/api/chat/reset", 
                             json={'session_id': session_id}, timeout=10)
                logger.info("Session cleaned up")
            except:
                pass

if __name__ == "__main__":
    success = test_complete_workflow()
    exit(0 if success else 1)