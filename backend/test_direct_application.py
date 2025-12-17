#!/usr/bin/env python3
"""
Test Direct Loan Application
"""

import requests
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_direct_application():
    """Test direct loan application"""
    base_url = "http://localhost:5000"
    
    # Direct application message
    application_message = """
    I want to apply for a personal loan. Here are my details:
    
    Name: John Doe
    Age: 35
    Monthly Income: ₹80,000
    Employment: Software Engineer at TechCorp (5 years)
    Credit Score: 750
    Loan Amount Required: ₹5,00,000
    Purpose: Home renovation
    
    Please process my application and provide the sanction letter if approved.
    """
    
    logger.info("Submitting direct loan application...")
    
    payload = {'message': application_message}
    response = requests.post(f"{base_url}/api/chat/message", 
                           json=payload, timeout=60)
    
    if response.status_code == 200:
        data = response.json()
        session_id = data.get('context', {}).get('sessionId')
        message = data.get('message', '')
        metadata = data.get('metadata', {})
        
        logger.info(f"Session: {session_id}")
        logger.info(f"Message: {message[:200]}...")
        logger.info(f"Metadata keys: {list(metadata.keys())}")
        
        # Check for approval and PDF
        if 'download_url' in metadata:
            download_url = metadata['download_url']
            logger.info(f"PDF download link: {download_url}")
            
            # Test download
            pdf_response = requests.get(f"{base_url}{download_url}")
            if pdf_response.status_code == 200:
                logger.info(f"PDF downloaded successfully! Size: {len(pdf_response.content)} bytes")
                return True
            else:
                logger.error(f"PDF download failed: {pdf_response.status_code}")
        
        # If not immediate approval, try to continue the conversation
        if 'approved' in message.lower() or 'sanction' in message.lower():
            logger.info("Loan appears approved, but no PDF link yet")
            
            # Try asking for the sanction letter explicitly
            follow_up = "Please generate and provide the sanction letter PDF for download."
            payload = {'message': follow_up, 'session_id': session_id}
            response2 = requests.post(f"{base_url}/api/chat/message", 
                                    json=payload, timeout=60)
            
            if response2.status_code == 200:
                data2 = response2.json()
                metadata2 = data2.get('metadata', {})
                
                if 'download_url' in metadata2:
                    download_url = metadata2['download_url']
                    logger.info(f"PDF download link from follow-up: {download_url}")
                    
                    pdf_response = requests.get(f"{base_url}{download_url}")
                    if pdf_response.status_code == 200:
                        logger.info(f"PDF downloaded successfully! Size: {len(pdf_response.content)} bytes")
                        return True
        
        logger.info("No PDF generated yet")
        return False
    
    else:
        logger.error(f"Application failed: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    success = test_direct_application()
    print(f"Direct Application Test: {'PASS' if success else 'FAIL'}")