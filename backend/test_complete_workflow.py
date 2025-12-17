#!/usr/bin/env python3
"""
Test Complete Loan Workflow with Multiple Steps
"""

import requests
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_message(base_url, session_id, message):
    """Send a message and return the response"""
    payload = {'message': message}
    if session_id:
        payload['session_id'] = session_id
    
    response = requests.post(f"{base_url}/api/chat/message", 
                           json=payload, timeout=60)
    
    if response.status_code == 200:
        data = response.json()
        new_session_id = data.get('context', {}).get('sessionId', session_id)
        return new_session_id, data
    else:
        logger.error(f"Request failed: {response.status_code} - {response.text}")
        return session_id, None

def test_complete_loan_workflow():
    """Test the complete loan workflow step by step"""
    base_url = "http://localhost:5000"
    session_id = None
    
    # Step 1: Initial greeting
    logger.info("Step 1: Initial greeting...")
    session_id, response = send_message(base_url, session_id, "Hello, I need a loan")
    if not response:
        return False
    
    logger.info(f"Session: {session_id}")
    logger.info(f"Response: {response.get('message', '')[:100]}...")
    
    # Step 2: Provide personal details
    logger.info("Step 2: Providing personal details...")
    personal_details = "My name is John Doe, I am 35 years old, and I work as a Software Engineer."
    session_id, response = send_message(base_url, session_id, personal_details)
    if not response:
        return False
    
    logger.info(f"Response: {response.get('message', '')[:100]}...")
    
    # Step 3: Provide financial details
    logger.info("Step 3: Providing financial details...")
    financial_details = "My monthly income is ₹80,000. I work at TechCorp for 5 years. My credit score is 750."
    session_id, response = send_message(base_url, session_id, financial_details)
    if not response:
        return False
    
    logger.info(f"Response: {response.get('message', '')[:100]}...")
    
    # Step 4: Request specific loan amount
    logger.info("Step 4: Requesting loan amount...")
    loan_request = "I want a personal loan of ₹5,00,000 for home renovation."
    session_id, response = send_message(base_url, session_id, loan_request)
    if not response:
        return False
    
    logger.info(f"Response: {response.get('message', '')[:100]}...")
    
    # Check for approval and PDF link
    metadata = response.get('metadata', {})
    message = response.get('message', '')
    
    if 'download_url' in metadata:
        download_url = metadata['download_url']
        logger.info(f"PDF download link found: {download_url}")
        
        # Test PDF download
        pdf_response = requests.get(f"{base_url}{download_url}")
        if pdf_response.status_code == 200:
            logger.info("PDF download successful!")
            logger.info(f"PDF size: {len(pdf_response.content)} bytes")
            return True
        else:
            logger.error(f"PDF download failed: {pdf_response.status_code}")
    
    if 'approved' in message.lower():
        logger.info("Loan approved but no PDF link yet")
    else:
        logger.info("Loan not yet approved or needs more information")
    
    return False

if __name__ == "__main__":
    success = test_complete_loan_workflow()
    print(f"Complete Workflow Test: {'PASS' if success else 'FAIL'}")