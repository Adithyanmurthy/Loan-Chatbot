#!/usr/bin/env python3
"""
Simple Integration Test to Debug Issues
"""

import requests
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_basic_endpoints():
    """Test basic endpoints to identify issues"""
    base_url = "http://localhost:5000"
    
    # Test 1: Health check
    logger.info("Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        logger.info(f"Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False
    
    # Test 2: Simple chat message
    logger.info("Testing simple chat message...")
    try:
        payload = {
            'message': 'Hello'
        }
        response = requests.post(f"{base_url}/api/chat/message", 
                               json=payload, timeout=30)
        logger.info(f"Chat message: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Response keys: {list(data.keys())}")
            session_id = data.get('session_id')
            logger.info(f"Session ID: {session_id}")
        else:
            logger.error(f"Chat message failed: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Chat message failed: {e}")
        return False
    
    # Test 3: Chat status
    if session_id:
        logger.info("Testing chat status...")
        try:
            response = requests.get(f"{base_url}/api/chat/status", 
                                  params={'session_id': session_id}, timeout=10)
            logger.info(f"Chat status: {response.status_code}")
            if response.status_code == 200:
                logger.info("Status check successful")
            else:
                logger.error(f"Status check failed: {response.text}")
        except Exception as e:
            logger.error(f"Status check failed: {e}")
    
    return True

if __name__ == "__main__":
    success = test_basic_endpoints()
    print(f"Test result: {'PASS' if success else 'FAIL'}")