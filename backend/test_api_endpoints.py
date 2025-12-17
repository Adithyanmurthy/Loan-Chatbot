#!/usr/bin/env python3
"""
Simple test script to verify API endpoints are working
"""

import requests
import json
import sys
import time

def test_health_endpoint():
    """Test the health check endpoint"""
    try:
        response = requests.get('http://localhost:5000/health', timeout=5)
        if response.status_code == 200:
            print("✓ Health endpoint working")
            return True
        else:
            print(f"✗ Health endpoint failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Health endpoint error: {e}")
        return False

def test_chat_message_endpoint():
    """Test the chat message endpoint"""
    try:
        payload = {
            "message": "Hello, I'm interested in a loan",
            "customer_id": "test_customer_123"
        }
        
        response = requests.post(
            'http://localhost:5000/api/chat/message',
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('session_id'):
                print("✓ Chat message endpoint working")
                print(f"  Session ID: {data['session_id']}")
                return True, data['session_id']
            else:
                print(f"✗ Chat message endpoint failed: {data}")
                return False, None
        else:
            print(f"✗ Chat message endpoint failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False, None
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Chat message endpoint error: {e}")
        return False, None

def test_chat_status_endpoint(session_id):
    """Test the chat status endpoint"""
    try:
        response = requests.get(
            f'http://localhost:5000/api/chat/status?session_id={session_id}',
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✓ Chat status endpoint working")
                print(f"  Conversation stage: {data.get('conversation_stage')}")
                return True
            else:
                print(f"✗ Chat status endpoint failed: {data}")
                return False
        else:
            print(f"✗ Chat status endpoint failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Chat status endpoint error: {e}")
        return False

def test_document_endpoints():
    """Test document-related endpoints"""
    try:
        # Test sanction letters list
        response = requests.get('http://localhost:5000/api/documents/sanction-letters', timeout=5)
        if response.status_code == 200:
            print("✓ Sanction letters list endpoint working")
        else:
            print(f"✗ Sanction letters list failed: {response.status_code}")
            
        # Test document uploads list
        response = requests.get('http://localhost:5000/api/documents/uploads', timeout=5)
        if response.status_code == 200:
            print("✓ Document uploads list endpoint working")
            return True
        else:
            print(f"✗ Document uploads list failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Document endpoints error: {e}")
        return False

def main():
    """Run all endpoint tests"""
    print("Testing Flask API endpoints...")
    print("=" * 50)
    
    # Test health endpoint first
    if not test_health_endpoint():
        print("\n❌ Server appears to be down. Please start the Flask server first.")
        print("Run: python app.py")
        sys.exit(1)
    
    # Test chat endpoints
    success, session_id = test_chat_message_endpoint()
    if success and session_id:
        test_chat_status_endpoint(session_id)
    
    # Test document endpoints
    test_document_endpoints()
    
    print("\n" + "=" * 50)
    print("✅ API endpoint testing completed!")
    print("\nTo start the server, run: python app.py")

if __name__ == "__main__":
    main()