#!/usr/bin/env python3
"""
Test PDF Generation Workflow
"""

import requests
import json
import time
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_loan_approval_and_pdf():
    """Test complete loan approval workflow with PDF generation"""
    base_url = "http://localhost:5000"
    
    # Test loan application that should get approved
    loan_request = {
        'message': 'I want to apply for a personal loan of ₹5,00,000. My name is John Doe, age 35, monthly income ₹80,000, employed as Software Engineer at TechCorp for 5 years. Credit score 750. No existing loans.'
    }
    
    logger.info("Submitting loan application...")
    try:
        response = requests.post(f"{base_url}/api/chat/message", 
                               json=loan_request, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            session_id = data.get('context', {}).get('sessionId')
            logger.info(f"Application submitted. Session: {session_id}")
            logger.info(f"Response data keys: {list(data.keys())}")
            logger.info(f"Message: {data.get('message', '')[:200]}...")
            
            # Check for download link in response metadata
            metadata = data.get('metadata', {})
            if 'download_url' in metadata:
                download_url = metadata['download_url']
                logger.info(f"PDF download link received: {download_url}")
                
                # Test PDF download
                pdf_response = requests.get(f"{base_url}{download_url}")
                if pdf_response.status_code == 200:
                    logger.info("PDF download successful!")
                    return True
                else:
                    logger.error(f"PDF download failed: {pdf_response.status_code}")
            else:
                logger.info("No download link in initial response")
                logger.info(f"Available metadata keys: {list(metadata.keys())}")
                
                # Check if the message contains approval and suggests next steps
                message = data.get('message', '')
                if 'approved' in message.lower() or 'sanction' in message.lower():
                    logger.info("Loan appears to be approved, but no PDF link generated yet")
                    return False
                
        else:
            logger.error(f"Application failed: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False
    
    return False

if __name__ == "__main__":
    success = test_loan_approval_and_pdf()
    print(f"PDF Generation Test: {'PASS' if success else 'FAIL'}")