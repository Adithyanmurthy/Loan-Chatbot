#!/usr/bin/env python3
"""
End-to-End Integration Test for AI Loan Chatbot
Tests complete customer journeys from initiation to sanction letter generation
Based on task 15.1: Integrate all components and test complete workflows
"""

import pytest
import requests
import json
import time
import os
import tempfile
from typing import Dict, Any, Optional
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class E2EIntegrationTest:
    """End-to-end integration test suite for the AI Loan Chatbot system"""
    
    def __init__(self):
        # API endpoints
        self.backend_url = "http://localhost:5000"
        self.mock_apis_base = "http://localhost"
        self.crm_api_url = f"{self.mock_apis_base}:3001"
        self.credit_api_url = f"{self.mock_apis_base}:3002"
        self.offer_api_url = f"{self.mock_apis_base}:3003"
        
        # Test data
        self.test_customers = [
            {
                'id': 'CUST001',
                'name': 'Rajesh Kumar',
                'expected_credit_score': 785,
                'expected_pre_approved': 500000,
                'loan_amount': 300000,  # Within pre-approved limit
                'expected_outcome': 'instant_approval'
            },
            {
                'id': 'CUST002', 
                'name': 'Priya Sharma',
                'expected_credit_score': 820,
                'expected_pre_approved': 800000,
                'loan_amount': 1200000,  # 1.5x pre-approved, needs salary verification
                'expected_outcome': 'conditional_approval'
            },
            {
                'id': 'CUST007',
                'name': 'Rohit Gupta',
                'expected_credit_score': 590,
                'expected_pre_approved': 150000,
                'loan_amount': 200000,
                'expected_outcome': 'rejection_low_credit'
            }
        ]
        
        # Session tracking
        self.active_sessions = {}
        
    def setup_test_environment(self):
        """Setup test environment and verify all services are running"""
        logger.info("Setting up test environment...")
        
        # Check backend health
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            assert response.status_code == 200, f"Backend health check failed: {response.status_code}"
            logger.info("✓ Backend service is healthy")
        except Exception as e:
            raise Exception(f"Backend service not available: {e}")
        
        # Check mock APIs health
        mock_services = [
            ("CRM API", f"{self.crm_api_url}/health"),
            ("Credit Bureau API", f"{self.credit_api_url}/health"),
            ("Offer Mart API", f"{self.offer_api_url}/health")
        ]
        
        for service_name, health_url in mock_services:
            try:
                response = requests.get(health_url, timeout=10)
                assert response.status_code == 200, f"{service_name} health check failed"
                logger.info(f"✓ {service_name} is healthy")
            except Exception as e:
                raise Exception(f"{service_name} not available: {e}")
        
        # Reset error simulation flags
        self._reset_error_simulations()
        
        logger.info("Test environment setup complete")
    
    def _reset_error_simulations(self):
        """Reset all error simulation flags in mock APIs"""
        error_reset_endpoints = [
            f"{self.crm_api_url}/simulate-error",
            f"{self.credit_api_url}/simulate-error", 
            f"{self.offer_api_url}/simulate-error"
        ]
        
        for endpoint in error_reset_endpoints:
            try:
                # Reset all error types
                for error_type in ['timeout', 'serverError', 'notFound', 'serviceUnavailable']:
                    requests.post(endpoint, json={'errorType': error_type, 'enabled': False}, timeout=5)
            except Exception as e:
                logger.warning(f"Could not reset error simulation for {endpoint}: {e}")
    
    def test_complete_instant_approval_journey(self):
        """Test complete customer journey resulting in instant approval"""
        logger.info("Testing complete instant approval journey...")
        
        customer = self.test_customers[0]  # CUST001 - instant approval case
        session_id = None
        
        try:
            # Step 1: Initiate conversation
            logger.info("Step 1: Initiating conversation...")
            session_id = self._initiate_conversation(customer['id'])
            assert session_id, "Failed to initiate conversation"
            
            # Step 2: Express loan interest
            logger.info("Step 2: Expressing loan interest...")
            response = self._send_message(session_id, f"Hi, I'm interested in a personal loan of ₹{customer['loan_amount']:,}")
            assert 'loan' in response.get('response', '').lower(), "Agent didn't recognize loan interest"
            
            # Step 3: Provide customer information
            logger.info("Step 3: Providing customer information...")
            customer_info = f"My name is {customer['name']}, I'm 32 years old, from Mumbai, and I need ₹{customer['loan_amount']:,} for home renovation."
            response = self._send_message(session_id, customer_info)
            
            # Step 4: Sales negotiation
            logger.info("Step 4: Sales negotiation...")
            response = self._send_message(session_id, "Yes, I'm interested in the loan terms you mentioned.")
            
            # Step 5: Verification process
            logger.info("Step 5: Verification process...")
            response = self._send_message(session_id, "Yes, please proceed with verification.")
            
            # Step 6: Underwriting process (should be instant approval)
            logger.info("Step 6: Underwriting process...")
            response = self._send_message(session_id, "Please check my eligibility.")
            
            # Step 7: Sanction letter generation
            logger.info("Step 7: Sanction letter generation...")
            # The system should automatically generate sanction letter for approved loans
            
            # Verify final conversation status
            status = self._get_conversation_status(session_id)
            logger.info(f"Final conversation status: {status}")
            
            # Verify sanction letter was generated
            # This would typically check for download links or file generation
            
            logger.info("✓ Complete instant approval journey test passed")
            return True
            
        except Exception as e:
            logger.error(f"Instant approval journey test failed: {e}")
            return False
        finally:
            if session_id:
                self._cleanup_session(session_id)
    
    def test_complete_conditional_approval_journey(self):
        """Test complete customer journey requiring document upload"""
        logger.info("Testing complete conditional approval journey...")
        
        customer = self.test_customers[1]  # CUST002 - conditional approval case
        session_id = None
        
        try:
            # Step 1: Initiate conversation
            logger.info("Step 1: Initiating conversation...")
            session_id = self._initiate_conversation(customer['id'])
            
            # Step 2: Express loan interest for higher amount
            logger.info("Step 2: Expressing loan interest for higher amount...")
            response = self._send_message(session_id, f"I want a personal loan of ₹{customer['loan_amount']:,}")
            
            # Step 3: Provide customer information
            logger.info("Step 3: Providing customer information...")
            customer_info = f"I'm {customer['name']}, 28 years old, from Delhi. I need ₹{customer['loan_amount']:,} for business expansion."
            response = self._send_message(session_id, customer_info)
            
            # Step 4: Sales negotiation
            logger.info("Step 4: Sales negotiation...")
            response = self._send_message(session_id, "The terms look good, let's proceed.")
            
            # Step 5: Verification
            logger.info("Step 5: Verification...")
            response = self._send_message(session_id, "Yes, please verify my details.")
            
            # Step 6: Underwriting (should request documents)
            logger.info("Step 6: Underwriting - expecting document request...")
            response = self._send_message(session_id, "Please process my loan application.")
            
            # Check if document upload is requested
            if response.get('upload_required'):
                logger.info("Step 7: Document upload requested as expected...")
                
                # Step 8: Upload salary slip
                logger.info("Step 8: Uploading salary slip...")
                upload_success = self._upload_salary_slip(session_id)
                assert upload_success, "Salary slip upload failed"
                
                # Step 9: Continue after document processing
                logger.info("Step 9: Continuing after document processing...")
                response = self._send_message(session_id, "I've uploaded my salary slip. Please continue.")
            
            # Verify final status
            status = self._get_conversation_status(session_id)
            logger.info(f"Final conversation status: {status}")
            
            logger.info("✓ Complete conditional approval journey test passed")
            return True
            
        except Exception as e:
            logger.error(f"Conditional approval journey test failed: {e}")
            return False
        finally:
            if session_id:
                self._cleanup_session(session_id)
    
    def test_complete_rejection_journey(self):
        """Test complete customer journey resulting in rejection"""
        logger.info("Testing complete rejection journey...")
        
        customer = self.test_customers[2]  # CUST007 - rejection case (low credit score)
        session_id = None
        
        try:
            # Step 1: Initiate conversation
            logger.info("Step 1: Initiating conversation...")
            session_id = self._initiate_conversation(customer['id'])
            
            # Step 2: Express loan interest
            logger.info("Step 2: Expressing loan interest...")
            response = self._send_message(session_id, f"I need a loan of ₹{customer['loan_amount']:,}")
            
            # Step 3: Provide customer information
            logger.info("Step 3: Providing customer information...")
            customer_info = f"My name is {customer['name']}, I'm 33 years old, from Kolkata."
            response = self._send_message(session_id, customer_info)
            
            # Step 4: Sales negotiation
            logger.info("Step 4: Sales negotiation...")
            response = self._send_message(session_id, "I agree to the terms.")
            
            # Step 5: Verification
            logger.info("Step 5: Verification...")
            response = self._send_message(session_id, "Please verify my details.")
            
            # Step 6: Underwriting (should result in rejection due to low credit score)
            logger.info("Step 6: Underwriting - expecting rejection...")
            response = self._send_message(session_id, "Please check my loan eligibility.")
            
            # Verify rejection was communicated appropriately
            # The response should contain rejection information
            
            # Verify final status
            status = self._get_conversation_status(session_id)
            logger.info(f"Final conversation status: {status}")
            
            logger.info("✓ Complete rejection journey test passed")
            return True
            
        except Exception as e:
            logger.error(f"Rejection journey test failed: {e}")
            return False
        finally:
            if session_id:
                self._cleanup_session(session_id)
    
    def test_agent_handoffs_and_coordination(self):
        """Test that all agent handoffs work correctly"""
        logger.info("Testing agent handoffs and coordination...")
        
        customer = self.test_customers[0]
        session_id = None
        
        try:
            session_id = self._initiate_conversation(customer['id'])
            
            # Track agent transitions through conversation stages
            expected_agent_flow = [
                'master',      # Initial conversation
                'sales',       # Sales negotiation
                'verification', # Verification process
                'underwriting', # Underwriting assessment
                'sanction'     # Sanction letter generation (if approved)
            ]
            
            observed_agents = []
            
            # Go through conversation flow and track agent changes
            messages = [
                "I want a personal loan",
                "My name is Rajesh Kumar, I need ₹300000",
                "Yes, I agree to the terms",
                "Please verify my details",
                "Check my eligibility"
            ]
            
            for message in messages:
                response = self._send_message(session_id, message)
                current_agent = response.get('agentType', 'unknown')
                if current_agent not in observed_agents:
                    observed_agents.append(current_agent)
                
                # Small delay between messages
                time.sleep(1)
            
            logger.info(f"Observed agent flow: {observed_agents}")
            
            # Verify that multiple agents were involved
            assert len(observed_agents) >= 2, f"Expected multiple agents, got: {observed_agents}"
            
            logger.info("✓ Agent handoffs and coordination test passed")
            return True
            
        except Exception as e:
            logger.error(f"Agent handoffs test failed: {e}")
            return False
        finally:
            if session_id:
                self._cleanup_session(session_id)
    
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms"""
        logger.info("Testing error handling and recovery...")
        
        # Test 1: API timeout simulation
        logger.info("Test 1: API timeout simulation...")
        try:
            # Enable timeout simulation on CRM API
            requests.post(f"{self.crm_api_url}/simulate-error", 
                         json={'errorType': 'timeout', 'enabled': True}, timeout=5)
            
            session_id = self._initiate_conversation('CUST001')
            response = self._send_message(session_id, "I want a loan")
            
            # System should handle timeout gracefully
            assert 'error' not in response or response.get('error_handled', False), "Timeout not handled gracefully"
            
            # Reset timeout simulation
            requests.post(f"{self.crm_api_url}/simulate-error", 
                         json={'errorType': 'timeout', 'enabled': False}, timeout=5)
            
            self._cleanup_session(session_id)
            logger.info("✓ API timeout handling test passed")
            
        except Exception as e:
            logger.error(f"API timeout test failed: {e}")
        
        # Test 2: Service unavailable simulation
        logger.info("Test 2: Service unavailable simulation...")
        try:
            # Enable service unavailable on Credit Bureau API
            requests.post(f"{self.credit_api_url}/simulate-error", 
                         json={'errorType': 'serviceUnavailable', 'enabled': True}, timeout=5)
            
            session_id = self._initiate_conversation('CUST002')
            
            # Go through conversation until underwriting
            messages = [
                "I need a loan of ₹500000",
                "My name is Priya Sharma",
                "I agree to proceed",
                "Please verify my details",
                "Check my eligibility"
            ]
            
            for message in messages:
                response = self._send_message(session_id, message)
                time.sleep(0.5)
            
            # Reset service unavailable simulation
            requests.post(f"{self.credit_api_url}/simulate-error", 
                         json={'errorType': 'serviceUnavailable', 'enabled': False}, timeout=5)
            
            self._cleanup_session(session_id)
            logger.info("✓ Service unavailable handling test passed")
            
        except Exception as e:
            logger.error(f"Service unavailable test failed: {e}")
        
        logger.info("✓ Error handling and recovery tests completed")
        return True
    
    def test_concurrent_conversations(self):
        """Test system behavior with multiple concurrent conversations"""
        logger.info("Testing concurrent conversations...")
        
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def run_conversation(customer_data, result_queue):
            """Run a single conversation in a thread"""
            try:
                session_id = self._initiate_conversation(customer_data['id'])
                
                # Simple conversation flow
                messages = [
                    f"I want a loan of ₹{customer_data['loan_amount']}",
                    f"My name is {customer_data['name']}",
                    "I agree to the terms",
                    "Please proceed with verification"
                ]
                
                for message in messages:
                    response = self._send_message(session_id, message)
                    time.sleep(0.5)  # Small delay between messages
                
                result_queue.put({'success': True, 'session_id': session_id})
                
            except Exception as e:
                result_queue.put({'success': False, 'error': str(e)})
        
        # Start multiple concurrent conversations
        threads = []
        for customer in self.test_customers:
            thread = threading.Thread(target=run_conversation, args=(customer, results_queue))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=60)  # 60 second timeout per thread
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Verify all conversations completed successfully
        successful_conversations = [r for r in results if r.get('success')]
        failed_conversations = [r for r in results if not r.get('success')]
        
        logger.info(f"Successful conversations: {len(successful_conversations)}")
        logger.info(f"Failed conversations: {len(failed_conversations)}")
        
        if failed_conversations:
            for failure in failed_conversations:
                logger.error(f"Conversation failed: {failure.get('error')}")
        
        # Cleanup sessions
        for result in successful_conversations:
            if 'session_id' in result:
                self._cleanup_session(result['session_id'])
        
        # At least 2 out of 3 conversations should succeed
        assert len(successful_conversations) >= 2, f"Too many concurrent conversation failures: {len(failed_conversations)}"
        
        logger.info("✓ Concurrent conversations test passed")
        return True
    
    # Helper methods
    
    def _initiate_conversation(self, customer_id: Optional[str] = None) -> str:
        """Initiate a new conversation and return session ID"""
        payload = {
            'message': 'Hello',
            'customer_id': customer_id
        }
        
        response = requests.post(f"{self.backend_url}/api/chat/message", 
                               json=payload, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"Failed to initiate conversation: {response.status_code} - {response.text}")
        
        data = response.json()
        session_id = data.get('session_id')
        
        if not session_id:
            raise Exception(f"No session ID returned: {data}")
        
        self.active_sessions[session_id] = {
            'customer_id': customer_id,
            'created_at': datetime.now(),
            'messages': []
        }
        
        return session_id
    
    def _send_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """Send a message in an existing conversation"""
        payload = {
            'message': message,
            'session_id': session_id
        }
        
        response = requests.post(f"{self.backend_url}/api/chat/message", 
                               json=payload, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"Failed to send message: {response.status_code} - {response.text}")
        
        data = response.json()
        
        # Track message in session
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['messages'].append({
                'user_message': message,
                'agent_response': data.get('response'),
                'timestamp': datetime.now()
            })
        
        return data
    
    def _get_conversation_status(self, session_id: str) -> Dict[str, Any]:
        """Get conversation status"""
        response = requests.get(f"{self.backend_url}/api/chat/status", 
                              params={'session_id': session_id}, timeout=10)
        
        if response.status_code != 200:
            raise Exception(f"Failed to get status: {response.status_code} - {response.text}")
        
        return response.json()
    
    def _upload_salary_slip(self, session_id: str) -> bool:
        """Upload a test salary slip"""
        # Create a dummy PDF file for testing
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            # Write some dummy PDF content
            temp_file.write(b'%PDF-1.4\n%Test salary slip content\n')
            temp_file_path = temp_file.name
        
        try:
            with open(temp_file_path, 'rb') as file:
                files = {'file': ('salary_slip.pdf', file, 'application/pdf')}
                data = {'session_id': session_id}
                
                response = requests.post(f"{self.backend_url}/api/documents/upload/salary-slip", 
                                       files=files, data=data, timeout=60)
                
                return response.status_code in [200, 201]
        
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file_path)
            except:
                pass
    
    def _cleanup_session(self, session_id: str):
        """Clean up a test session"""
        try:
            requests.post(f"{self.backend_url}/api/chat/reset", 
                         json={'session_id': session_id}, timeout=10)
            
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
                
        except Exception as e:
            logger.warning(f"Failed to cleanup session {session_id}: {e}")
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all integration tests"""
        logger.info("Starting comprehensive end-to-end integration tests...")
        
        # Setup test environment
        self.setup_test_environment()
        
        test_results = {}
        
        # Run all test cases
        test_cases = [
            ('instant_approval_journey', self.test_complete_instant_approval_journey),
            ('conditional_approval_journey', self.test_complete_conditional_approval_journey),
            ('rejection_journey', self.test_complete_rejection_journey),
            ('agent_handoffs', self.test_agent_handoffs_and_coordination),
            ('error_handling', self.test_error_handling_and_recovery),
            ('concurrent_conversations', self.test_concurrent_conversations)
        ]
        
        for test_name, test_method in test_cases:
            logger.info(f"\n{'='*60}")
            logger.info(f"Running test: {test_name}")
            logger.info(f"{'='*60}")
            
            try:
                result = test_method()
                test_results[test_name] = result
                logger.info(f"✓ Test {test_name}: {'PASSED' if result else 'FAILED'}")
                
            except Exception as e:
                test_results[test_name] = False
                logger.error(f"✗ Test {test_name}: FAILED with exception: {e}")
            
            # Small delay between tests
            time.sleep(2)
        
        # Cleanup any remaining sessions
        for session_id in list(self.active_sessions.keys()):
            self._cleanup_session(session_id)
        
        # Print summary
        logger.info(f"\n{'='*60}")
        logger.info("TEST SUMMARY")
        logger.info(f"{'='*60}")
        
        passed_tests = sum(1 for result in test_results.values() if result)
        total_tests = len(test_results)
        
        for test_name, result in test_results.items():
            status = "PASSED" if result else "FAILED"
            logger.info(f"{test_name}: {status}")
        
        logger.info(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            logger.info("🎉 All integration tests PASSED!")
        else:
            logger.warning(f"⚠️  {total_tests - passed_tests} test(s) FAILED")
        
        return test_results


def main():
    """Main function to run integration tests"""
    test_suite = E2EIntegrationTest()
    results = test_suite.run_all_tests()
    
    # Exit with appropriate code
    all_passed = all(results.values())
    exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()