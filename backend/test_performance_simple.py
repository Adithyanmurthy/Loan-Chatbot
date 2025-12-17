#!/usr/bin/env python3
"""
Simple Performance Test for AI Loan Chatbot
Tests response times and basic concurrent load
"""

import requests
import time
import statistics
import threading
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimplePerformanceTest:
    """Simple performance test suite"""
    
    def __init__(self):
        self.backend_url = "http://localhost:5000"
        self.target_response_time = 5 * 60  # 5 minutes in seconds
    
    def test_single_conversation_performance(self) -> Dict[str, Any]:
        """Test performance of a single conversation"""
        logger.info("Testing single conversation performance...")
        
        response_times = []
        total_start = time.time()
        
        try:
            # Initiate conversation
            start = time.time()
            response = requests.post(f"{self.backend_url}/api/chat/message", 
                                   json={'message': 'Hello', 'customer_id': 'CUST001'}, 
                                   timeout=30)
            response_times.append(time.time() - start)
            
            if response.status_code != 200:
                return {'error': f'Init failed: {response.status_code}'}
            
            session_id = response.json().get('session_id')
            
            # Send conversation messages
            messages = [
                "I want a personal loan of ₹300000",
                "My name is Rajesh Kumar, I am 32 years old",
                "Yes, I agree to the terms",
                "Please proceed with verification",
                "Check my eligibility"
            ]
            
            for message in messages:
                start = time.time()
                response = requests.post(f"{self.backend_url}/api/chat/message", 
                                       json={'message': message, 'session_id': session_id}, 
                                       timeout=30)
                response_times.append(time.time() - start)
                
                if response.status_code != 200:
                    logger.warning(f"Message failed: {response.status_code}")
                
                time.sleep(0.5)  # Small delay between messages
            
            total_time = time.time() - total_start
            
            return {
                'success': True,
                'total_time': total_time,
                'response_times': response_times,
                'average_response_time': statistics.mean(response_times),
                'max_response_time': max(response_times),
                'min_response_time': min(response_times),
                'target_met': all(t <= self.target_response_time for t in response_times)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def test_concurrent_conversations(self, num_users: int = 5) -> Dict[str, Any]:
        """Test concurrent conversations"""
        logger.info(f"Testing {num_users} concurrent conversations...")
        
        results = []
        threads = []
        
        def run_conversation(user_id: int):
            """Run a single conversation in a thread"""
            try:
                start_time = time.time()
                
                # Initiate conversation
                response = requests.post(f"{self.backend_url}/api/chat/message", 
                                       json={'message': f'Hello, I am user {user_id}', 
                                             'customer_id': f'CUST00{user_id}'}, 
                                       timeout=30)
                
                if response.status_code != 200:
                    results.append({'user_id': user_id, 'error': f'Init failed: {response.status_code}'})
                    return
                
                session_id = response.json().get('session_id')
                
                # Send a few messages
                messages = [
                    f"I want a loan of ₹{300000 + user_id * 10000}",
                    f"My name is User {user_id}",
                    "I agree to proceed"
                ]
                
                response_times = []
                for message in messages:
                    msg_start = time.time()
                    response = requests.post(f"{self.backend_url}/api/chat/message", 
                                           json={'message': message, 'session_id': session_id}, 
                                           timeout=30)
                    response_times.append(time.time() - msg_start)
                    
                    if response.status_code != 200:
                        break
                    
                    time.sleep(0.2)  # Small delay
                
                total_time = time.time() - start_time
                
                results.append({
                    'user_id': user_id,
                    'success': True,
                    'total_time': total_time,
                    'response_times': response_times,
                    'session_id': session_id
                })
                
            except Exception as e:
                results.append({'user_id': user_id, 'error': str(e)})
        
        # Start all threads
        for i in range(num_users):
            thread = threading.Thread(target=run_conversation, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=60)  # 60 second timeout per thread
        
        # Analyze results
        successful_conversations = [r for r in results if r.get('success')]
        failed_conversations = [r for r in results if not r.get('success')]
        
        all_response_times = []
        for conv in successful_conversations:
            all_response_times.extend(conv.get('response_times', []))
        
        return {
            'total_conversations': len(results),
            'successful_conversations': len(successful_conversations),
            'failed_conversations': len(failed_conversations),
            'success_rate': len(successful_conversations) / len(results) if results else 0,
            'average_response_time': statistics.mean(all_response_times) if all_response_times else 0,
            'max_response_time': max(all_response_times) if all_response_times else 0,
            'total_requests': len(all_response_times),
            'responses_over_5min': len([t for t in all_response_times if t > 300])
        }
    
    def test_response_time_under_load(self) -> Dict[str, Any]:
        """Test response times under different load levels"""
        logger.info("Testing response times under different load levels...")
        
        load_results = {}
        
        for concurrent_users in [1, 3, 5]:
            logger.info(f"Testing with {concurrent_users} concurrent users...")
            
            result = self.test_concurrent_conversations(concurrent_users)
            load_results[f"{concurrent_users}_users"] = result
            
            logger.info(f"  Success Rate: {result['success_rate']:.2%}")
            logger.info(f"  Avg Response Time: {result['average_response_time']:.2f}s")
            logger.info(f"  Max Response Time: {result['max_response_time']:.2f}s")
            
            # Small delay between tests
            time.sleep(5)
        
        return load_results
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run all performance tests"""
        logger.info("Starting performance test suite...")
        
        results = {
            'test_timestamp': time.time(),
            'target_response_time_seconds': self.target_response_time
        }
        
        # Test 1: Single conversation performance
        logger.info("\n" + "="*50)
        logger.info("SINGLE CONVERSATION PERFORMANCE")
        logger.info("="*50)
        
        single_result = self.test_single_conversation_performance()
        results['single_conversation'] = single_result
        
        if single_result.get('success'):
            logger.info(f"✓ Single conversation completed in {single_result['total_time']:.2f}s")
            logger.info(f"  Average response time: {single_result['average_response_time']:.2f}s")
            logger.info(f"  Max response time: {single_result['max_response_time']:.2f}s")
            logger.info(f"  Target met: {'✓' if single_result['target_met'] else '✗'}")
        else:
            logger.error(f"✗ Single conversation failed: {single_result.get('error')}")
        
        # Test 2: Concurrent load testing
        logger.info("\n" + "="*50)
        logger.info("CONCURRENT LOAD TESTING")
        logger.info("="*50)
        
        load_results = self.test_response_time_under_load()
        results['load_testing'] = load_results
        
        # Generate summary
        results['summary'] = self._generate_summary(results)
        
        return results
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test summary"""
        summary = {
            'overall_status': 'PASS',
            'issues': [],
            'recommendations': []
        }
        
        # Check single conversation performance
        single_result = results.get('single_conversation', {})
        if single_result.get('success'):
            if not single_result.get('target_met'):
                summary['issues'].append("Single conversation exceeds target response time")
                summary['overall_status'] = 'FAIL'
        else:
            summary['issues'].append("Single conversation test failed")
            summary['overall_status'] = 'FAIL'
        
        # Check load testing results
        load_results = results.get('load_testing', {})
        for load_level, metrics in load_results.items():
            success_rate = metrics.get('success_rate', 0)
            if success_rate < 0.8:  # 80% success rate threshold
                summary['issues'].append(f"Low success rate at {load_level}: {success_rate:.2%}")
                summary['overall_status'] = 'FAIL'
        
        # Generate recommendations
        if summary['issues']:
            summary['recommendations'] = [
                "Consider implementing connection pooling",
                "Add caching for frequently accessed data",
                "Optimize database queries",
                "Consider horizontal scaling for high load"
            ]
        
        return summary
    
    def print_results(self, results: Dict[str, Any]):
        """Print formatted test results"""
        print("\n" + "="*60)
        print("AI LOAN CHATBOT - PERFORMANCE TEST RESULTS")
        print("="*60)
        
        # Single conversation results
        single_result = results.get('single_conversation', {})
        if single_result.get('success'):
            print(f"\nSingle Conversation Performance:")
            print(f"  Total Time: {single_result['total_time']:.2f}s")
            print(f"  Average Response Time: {single_result['average_response_time']:.2f}s")
            print(f"  Max Response Time: {single_result['max_response_time']:.2f}s")
            print(f"  Target Met (< 5min): {'✓' if single_result['target_met'] else '✗'}")
        
        # Load testing results
        load_results = results.get('load_testing', {})
        if load_results:
            print(f"\nConcurrent Load Testing:")
            for load_level, metrics in load_results.items():
                users = load_level.replace('_users', '')
                print(f"  {users} Users:")
                print(f"    Success Rate: {metrics['success_rate']:.2%}")
                print(f"    Avg Response Time: {metrics['average_response_time']:.2f}s")
                print(f"    Max Response Time: {metrics['max_response_time']:.2f}s")
                print(f"    Responses > 5min: {metrics['responses_over_5min']}")
        
        # Summary
        summary = results.get('summary', {})
        print(f"\nOverall Status: {summary.get('overall_status', 'UNKNOWN')}")
        
        issues = summary.get('issues', [])
        if issues:
            print(f"\nIssues Found:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
        
        recommendations = summary.get('recommendations', [])
        if recommendations:
            print(f"\nRecommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        
        print("\n" + "="*60)


def main():
    """Main function"""
    # Check if backend is available
    try:
        response = requests.get("http://localhost:5000/health", timeout=10)
        if response.status_code != 200:
            logger.error("Backend service is not available")
            return False
    except Exception as e:
        logger.error(f"Cannot connect to backend service: {e}")
        return False
    
    # Run performance tests
    test_suite = SimplePerformanceTest()
    results = test_suite.run_performance_tests()
    
    # Print results
    test_suite.print_results(results)
    
    # Return success/failure
    summary = results.get('summary', {})
    return summary.get('overall_status') == 'PASS'


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)