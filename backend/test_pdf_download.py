#!/usr/bin/env python3
"""
Test PDF Download Directly
"""

import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pdf_download():
    """Test PDF download directly"""
    base_url = "http://localhost:5000"
    
    # Use the filename from the logs
    filename = "sanction_letter_302646f3-a0e4-4455-9679-274cc9db2037_d8992e1b.pdf"
    download_url = f"{base_url}/api/documents/download/sanction-letter/{filename}"
    
    logger.info(f"Testing download: {download_url}")
    
    response = requests.get(download_url)
    logger.info(f"Response status: {response.status_code}")
    logger.info(f"Response headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        logger.info(f"PDF downloaded successfully! Size: {len(response.content)} bytes")
        return True
    else:
        logger.error(f"Download failed: {response.text}")
        return False

if __name__ == "__main__":
    success = test_pdf_download()
    print(f"PDF Download Test: {'PASS' if success else 'FAIL'}")