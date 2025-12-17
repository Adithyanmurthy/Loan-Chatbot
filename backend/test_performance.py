#!/usr/bin/env python3
"""
Performance Testing Suite for AI Loan Chatbot
Tests system behavior with multiple concurrent conversations and response times
Based on task 15.2: Performance testing and optimization
"""

import asyncio
import aiohttp
import time
import statistics
import json
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
import concurrent.futures
import threading
import queue
import psutil
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceTestSuite:
    """Performance testing suite for the AI Loan Chatbot system"""
    
    def __init__(self):
        self.backend_url = "http://localhost:5000"
        self.target_response_time = 5 * 60  # 5 minutes in seconds
        self.concurrent_users = [1, 5, 10, 20, 50]  # Different load levels
        self.test_duration = 300  # 5 minutes per test
        
        # Performance metrics
        self.metrics = {
            'response_times': [],
            'throughput': [],
            'error_rates': [],
            'resource_usage': [],
            'concurrent_sessions': []
        }
        
        # Test scenarios
        self.test_scenarios = [
            {
                'name': 'instant_approval',
                'customer_id': 'CUST001',
                'messages': [
                    "Hi, I need a personal loan",
                    "My name is Rajesh Kumar, I need ₹300000 for home renovation",
                    "Yes, I agree to the loan terms",
                    "Please proceed with verification",
                    "Check my loan eligibility"
                ],
                'expected_duration': 60  # seconds
            },
            {
                'name': 'conditional_approval',
                'customer_id': 'CUST002',
                'messages': [
                    "I want a loan of ₹1200000",
                    "I'm Priya Sharma, 28 years old from Delhi",
                    "The terms look good, let's proceed",
                    "Yes, please verify my details",
                    "Please process my loan application"
                ],
                'expected_duration': 120  # seconds (includes document upload)
            },
            {
                'name': 'rejection_scenario',
                'customer_id': 'CUST007',
                'messages': [
                    "I need a loan of ₹200000",
                    "My name is Rohit Gupta from Kolkata",
                    "I agree to the terms",
                    "Please verify my details",
                    "Check my eligibility"
                ],
                'expected_duration': 90  # seconds
            }
        ]
    
    async def single_conversation_test(self, session: aiohttp.ClientSession, 
                                     scenario: Dict[str, Any], 
                                     user_id: int) -> Dict[str, Any]:
        """Run a single conversation test scenario"""
        start_time = time.time()
        conversation_metrics = {
            'user_id': user_id,
            'scenario': scenario['name'],
            'start_time': start_time,
            'response_times': [],
            'errors': [],
            'session_id': None,
            'completed': False,
            'total_duration': 0
        }
        
        try:
            # Initiate conversation
            init_start = time.time()
            async with session.post(f"{self.backend_url}/api/chat/message", 
                                  json={
                                      'message': 'Hello',
                                      'customer_id': scenario['customer_id']
                                  }) as response:
                
                init_duration = time.time() - init_start
                conversation_metrics['response_times'].append(init_duration)
                
                if response.status != 200:
                    conversation_metrics['errors'].append(f"Init failed: {response.status}")
                    return conversation_metrics
                
                data = await response.json()
                conversation_metrics['session_id'] = data.get('session_id')
            
            # Send conversation messages
            for i, message in enumerate(scenario['messages']):
                msg_start = time.time()
                
                async with session.post(f"{self.backend_url}/api/chat/message",
                                      json={
                                          'message': message,
                                          'session_id': conversation_metrics['session_id']
                                      }) as response:
                    
                    msg_duration = time.time() - msg_start
                    conversation_metrics['response_times'].append(msg_duration)
                    
                    if response.status != 200:
                        conversation_metrics['errors'].append(f"Message {i} failed: {response.status}")
                        continue
                    
                    # Small delay between messages to simulate human behavior
                    await asyncio.sleep(0.5)
            
            conversation_metrics['completed'] = True
            conversation_metrics['total_duration'] = time.time() - start_time
            
        except Exception as e:
            conversation_metrics['errors'].append(f"Exception: {str(e)}")
        
        return conversation_metrics
    
    async def concurrent_load_test(self, concurrent_users: int, 
                                 duration: int) -> Dict[str, Any]:
        """Run concurrent load test with specified number of users"""
        logger.info(f"Running load test with {concurrent_users} concurrent users for {duration} seconds")
        
        test_start = time.time()
        test_end = test_start + duration
        
        # Metrics collection
        all_conversations = []
        active_sessions = set()
        
        # Resource monitoring
        resource_monitor = ResourceMonitor()
        resource_monitor.start()
        
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                connector=aiohttp.TCPConnector(limit=100)
            ) as session:
                
                # Start concurrent conversations
                tasks = []
                user_counter = 0
                
                while time.time() < test_end:
                    # Start new conversations up to the concurrent limit
                    while len(tasks) < concurrent_users and time.time() < test_end:
                        scenario = self.test_scenarios[user_counter % len(self.test_scenarios)]
                        task = asyncio.create_task(
                            self.single_conversation_test(session, scenario, user_counter)
                        )
                        tasks.append(task)
                        user_counter += 1
                        
                        # Small delay between starting conversations
                        await asyncio.sleep(0.1)
                    
                    # Check for completed tasks
                    done_tasks = [task for task in tasks if task.done()]
                    for task in done_tasks:
                        try:
                            result = await task
                            all_conversations.append(result)
                            if result.get('session_id'):
                                active_sessions.discard(result['session_id'])
                        except Exception as e:
                            logger.error(f"Task failed: {e}")
                        
                        tasks.remove(task)
                    
                    await asyncio.sleep(1)  # Check every second
                
                # Wait for remaining tasks to complete
                if tasks:
                    logger.info(f"Waiting for {len(tasks)} remaining conversations to complete...")
                    remaining_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for result in remaining_results:
                        if isinstance(result, dict):
                            all_conversations.append(result)
        
        finally:
            resource_monitor.stop()
        
        # Calculate metrics
        test_metrics = self._calculate_load_test_metrics(
            all_conversations, concurrent_users, duration, resource_monitor.get_metrics()
        )
        
        return test_metrics
    
    def _calculate_load_test_metrics(self, conversations: List[Dict[str, Any]], 
                                   concurrent_users: int, duration: int,
                                   resource_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance metrics from load test results"""
        
        # Response time metrics
        all_response_times = []
        for conv in conversations:
            all_response_times.extend(conv.get('response_times', []))
        
        # Completion metrics
        completed_conversations = [c for c in conversations if c.get('completed')]
        failed_conversations = [c for c in conversations if not c.get('completed')]
        
        # Error analysis
        all_errors = []
        for conv in conversations:
            all_errors.extend(conv.get('errors', []))
        
        # Calculate statistics
        metrics = {
            'test_config': {
                'concurrent_users': concurrent_users,
                'duration': duration,
                'total_conversations_started': len(conversations)
            },
            'completion_metrics': {
                'completed_conversations': len(completed_conversations),
                'failed_conversations': len(failed_conversations),
                'completion_rate': len(completed_conversations) / len(conversations) if conversations else 0,
                'average_conversation_duration': statistics.mean([c['total_duration'] for c in completed_conversations]) if completed_conversations else 0
            },
            'response_time_metrics': {
                'total_requests': len(all_response_times),
                'average_response_time': statistics.mean(all_response_times) if all_response_times else 0,
                'median_response_time': statistics.median(all_response_times) if all_response_times else 0,
                'p95_response_time': self._percentile(all_response_times, 95) if all_response_times else 0,
                'p99_response_time': self._percentile(all_response_times, 99) if all_response_times else 0,
                'max_response_time': max(all_response_times) if all_response_times else 0,
                'responses_over_5min': len([t for t in all_response_times if t > 300])  # 5 minutes
            },
            'throughput_metrics': {
                'requests_per_second': len(all_response_times) / duration if duration > 0 else 0,
                'conversations_per_minute': len(completed_conversations) / (duration / 60) if duration > 0 else 0
            },
            'error_metrics': {
                'total_errors': len(all_errors),
                'error_rate': len(all_errors) / len(all_response_times) if all_response_times else 0,
                'error_types': self._categorize_errors(all_errors)
            },
            'resource_metrics': resource_metrics
        }
        
        return metrics
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _categorize_errors(self, errors: List[str]) -> Dict[str, int]:
        """Categorize errors by type"""
        categories = {
            'timeout': 0,
            'server_error': 0,
            'client_error': 0,
            'network_error': 0,
            'other': 0
        }
        
        for error in errors:
            error_lower = error.lower()
            if 'timeout' in error_lower:
                categories['timeout'] += 1
            elif '5' in error and ('50' in error or '51' in error or '52' in error or '53' in error):
                categories['server_error'] += 1
            elif '4' in error and ('40' in error or '41' in error or '42' in error or '43' in error):
                categories['client_error'] += 1
            elif 'network' in error_lower or 'connection' in error_lower:
                categories['network_error'] += 1
            else:
                categories['other'] += 1
        
        return categories
    
    async def response_time_benchmark(self) -> Dict[str, Any]:
        """Benchmark response times for different conversation stages"""
        logger.info("Running response time benchmark...")
        
        benchmark_results = {}
        
        async with aiohttp.ClientSession() as session:
            for scenario in self.test_scenarios:
                logger.info(f"Benchmarking scenario: {scenario['name']}")
                
                # Run scenario multiple times for statistical significance
                scenario_results = []
                
                for run in range(5):  # 5 runs per scenario
                    result = await self.single_conversation_test(session, scenario, run)
                    scenario_results.append(result)
                    
                    # Small delay between runs
                    await asyncio.sleep(2)
                
                # Calculate scenario metrics
                all_response_times = []
                for result in scenario_results:
                    all_response_times.extend(result.get('response_times', []))
                
                completed_runs = [r for r in scenario_results if r.get('completed')]
                
                benchmark_results[scenario['name']] = {
                    'runs_completed': len(completed_runs),
                    'total_runs': len(scenario_results),
                    'average_response_time': statistics.mean(all_response_times) if all_response_times else 0,
                    'median_response_time': statistics.median(all_response_times) if all_response_times else 0,
                    'max_response_time': max(all_response_times) if all_response_times else 0,
                    'average_total_duration': statistics.mean([r['total_duration'] for r in completed_runs]) if completed_runs else 0,
                    'target_met': all(t <= self.target_response_time for t in all_response_times) if all_response_times else False
                }
        
        return benchmark_results
    
    def test_memory_usage_under_load(self) -> Dict[str, Any]:
        """Test memory usage patterns under different load conditions"""
        logger.info("Testing memory usage under load...")
        
        memory_results = {}
        
        for concurrent_users in [1, 5, 10, 20]:
            logger.info(f"Testing memory usage with {concurrent_users} concurrent users...")
            
            # Start resource monitoring
            resource_monitor = ResourceMonitor()
            resource_monitor.start()
            
            try:
                # Run load test for shorter duration to focus on memory
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                test_result = loop.run_until_complete(
                    self.concurrent_load_test(concurrent_users, 60)  # 1 minute test
                )
                
                loop.close()
                
            finally:
                resource_monitor.stop()
            
            memory_metrics = resource_monitor.get_metrics()
            
            memory_results[f"{concurrent_users}_users"] = {
                'peak_memory_mb': memory_metrics.get('peak_memory_mb', 0),
                'average_memory_mb': memory_metrics.get('average_memory_mb', 0),
                'memory_growth_mb': memory_metrics.get('memory_growth_mb', 0),
                'peak_cpu_percent': memory_metrics.get('peak_cpu_percent', 0),
                'average_cpu_percent': memory_metrics.get('average_cpu_percent', 0)
            }
            
            # Small delay between tests
            time.sleep(10)
        
        return memory_results
    
    async def run_all_performance_tests(self) -> Dict[str, Any]:
        """Run all performance tests"""
        logger.info("Starting comprehensive performance test suite...")
        
        all_results = {
            'test_timestamp': datetime.now().isoformat(),
            'target_response_time_seconds': self.target_response_time,
            'response_time_benchmark': {},
            'load_test_results': {},
            'memory_usage_results': {},
            'summary': {}
        }
        
        # 1. Response time benchmark
        logger.info("\n" + "="*60)
        logger.info("RESPONSE TIME BENCHMARK")
        logger.info("="*60)
        
        all_results['response_time_benchmark'] = await self.response_time_benchmark()
        
        # 2. Load testing with different concurrent user levels
        logger.info("\n" + "="*60)
        logger.info("CONCURRENT LOAD TESTING")
        logger.info("="*60)
        
        for concurrent_users in self.concurrent_users:
            logger.info(f"\nTesting with {concurrent_users} concurrent users...")
            
            load_result = await self.concurrent_load_test(concurrent_users, 120)  # 2 minute tests
            all_results['load_test_results'][f"{concurrent_users}_users"] = load_result
            
            # Log key metrics
            completion_rate = load_result['completion_metrics']['completion_rate']
            avg_response_time = load_result['response_time_metrics']['average_response_time']
            p95_response_time = load_result['response_time_metrics']['p95_response_time']
            
            logger.info(f"  Completion Rate: {completion_rate:.2%}")
            logger.info(f"  Avg Response Time: {avg_response_time:.2f}s")
            logger.info(f"  P95 Response Time: {p95_response_time:.2f}s")
            
            # Small delay between load tests
            await asyncio.sleep(10)
        
        # 3. Memory usage testing
        logger.info("\n" + "="*60)
        logger.info("MEMORY USAGE TESTING")
        logger.info("="*60)
        
        all_results['memory_usage_results'] = self.test_memory_usage_under_load()
        
        # 4. Generate summary
        all_results['summary'] = self._generate_performance_summary(all_results)
        
        return all_results
    
    def _generate_performance_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance test summary"""
        summary = {
            'overall_status': 'PASS',
            'issues_found': [],
            'recommendations': [],
            'key_metrics': {}
        }
        
        # Check response time targets
        benchmark_results = results.get('response_time_benchmark', {})
        for scenario, metrics in benchmark_results.items():
            avg_time = metrics.get('average_response_time', 0)
            if avg_time > self.target_response_time:
                summary['issues_found'].append(
                    f"Scenario '{scenario}' exceeds target response time: {avg_time:.2f}s > {self.target_response_time}s"
                )
                summary['overall_status'] = 'FAIL'
        
        # Check load test results
        load_results = results.get('load_test_results', {})
        for load_level, metrics in load_results.items():
            completion_rate = metrics['completion_metrics']['completion_rate']
            error_rate = metrics['error_metrics']['error_rate']
            
            if completion_rate < 0.95:  # 95% completion rate threshold
                summary['issues_found'].append(
                    f"Low completion rate at {load_level}: {completion_rate:.2%}"
                )
                summary['overall_status'] = 'FAIL'
            
            if error_rate > 0.05:  # 5% error rate threshold
                summary['issues_found'].append(
                    f"High error rate at {load_level}: {error_rate:.2%}"
                )
                summary['overall_status'] = 'FAIL'
        
        # Generate recommendations
        if summary['issues_found']:
            summary['recommendations'].extend([
                "Consider implementing connection pooling for database connections",
                "Add caching for frequently accessed data (customer profiles, offers)",
                "Implement request queuing for high-load scenarios",
                "Consider horizontal scaling for the backend service",
                "Optimize database queries and add appropriate indexes"
            ])
        
        # Key metrics summary
        if load_results:
            max_load_test = max(load_results.keys(), key=lambda x: int(x.split('_')[0]))
            max_load_metrics = load_results[max_load_test]
            
            summary['key_metrics'] = {
                'max_concurrent_users_tested': int(max_load_test.split('_')[0]),
                'max_load_completion_rate': max_load_metrics['completion_metrics']['completion_rate'],
                'max_load_avg_response_time': max_load_metrics['response_time_metrics']['average_response_time'],
                'max_load_throughput_rps': max_load_metrics['throughput_metrics']['requests_per_second']
            }
        
        return summary
    
    def print_performance_report(self, results: Dict[str, Any]):
        """Print formatted performance test report"""
        print("\n" + "="*80)
        print("AI LOAN CHATBOT - PERFORMANCE TEST REPORT")
        print("="*80)
        
        print(f"\nTest Timestamp: {results['test_timestamp']}")
        print(f"Target Response Time: {results['target_response_time_seconds']} seconds")
        
        # Response Time Benchmark
        print("\n" + "-"*60)
        print("RESPONSE TIME BENCHMARK RESULTS")
        print("-"*60)
        
        benchmark = results.get('response_time_benchmark', {})
        for scenario, metrics in benchmark.items():
            print(f"\nScenario: {scenario}")
            print(f"  Completed Runs: {metrics['runs_completed']}/{metrics['total_runs']}")
            print(f"  Average Response Time: {metrics['average_response_time']:.2f}s")
            print(f"  Median Response Time: {metrics['median_response_time']:.2f}s")
            print(f"  Max Response Time: {metrics['max_response_time']:.2f}s")
            print(f"  Average Total Duration: {metrics['average_total_duration']:.2f}s")
            print(f"  Target Met: {'✓' if metrics['target_met'] else '✗'}")
        
        # Load Test Results
        print("\n" + "-"*60)
        print("CONCURRENT LOAD TEST RESULTS")
        print("-"*60)
        
        load_results = results.get('load_test_results', {})
        for load_level, metrics in load_results.items():
            users = load_level.replace('_users', '')
            print(f"\n{users} Concurrent Users:")
            print(f"  Completion Rate: {metrics['completion_metrics']['completion_rate']:.2%}")
            print(f"  Average Response Time: {metrics['response_time_metrics']['average_response_time']:.2f}s")
            print(f"  P95 Response Time: {metrics['response_time_metrics']['p95_response_time']:.2f}s")
            print(f"  Requests/Second: {metrics['throughput_metrics']['requests_per_second']:.2f}")
            print(f"  Error Rate: {metrics['error_metrics']['error_rate']:.2%}")
        
        # Memory Usage Results
        print("\n" + "-"*60)
        print("MEMORY USAGE RESULTS")
        print("-"*60)
        
        memory_results = results.get('memory_usage_results', {})
        for load_level, metrics in memory_results.items():
            users = load_level.replace('_users', '')
            print(f"\n{users} Concurrent Users:")
            print(f"  Peak Memory: {metrics['peak_memory_mb']:.1f} MB")
            print(f"  Average Memory: {metrics['average_memory_mb']:.1f} MB")
            print(f"  Memory Growth: {metrics['memory_growth_mb']:.1f} MB")
            print(f"  Peak CPU: {metrics['peak_cpu_percent']:.1f}%")
            print(f"  Average CPU: {metrics['average_cpu_percent']:.1f}%")
        
        # Summary
        print("\n" + "-"*60)
        print("PERFORMANCE TEST SUMMARY")
        print("-"*60)
        
        summary = results.get('summary', {})
        status = summary.get('overall_status', 'UNKNOWN')
        print(f"\nOverall Status: {status}")
        
        issues = summary.get('issues_found', [])
        if issues:
            print(f"\nIssues Found ({len(issues)}):")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
        else:
            print("\n✓ No performance issues found")
        
        recommendations = summary.get('recommendations', [])
        if recommendations:
            print(f"\nRecommendations ({len(recommendations)}):")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        
        key_metrics = summary.get('key_metrics', {})
        if key_metrics:
            print(f"\nKey Metrics:")
            for metric, value in key_metrics.items():
                print(f"  {metric.replace('_', ' ').title()}: {value}")
        
        print("\n" + "="*80)


class ResourceMonitor:
    """Monitor system resource usage during tests"""
    
    def __init__(self):
        self.monitoring = False
        self.metrics = []
        self.monitor_thread = None
        self.start_time = None
    
    def start(self):
        """Start resource monitoring"""
        self.monitoring = True
        self.start_time = time.time()
        self.metrics = []
        self.monitor_thread = threading.Thread(target=self._monitor_resources)
        self.monitor_thread.start()
    
    def stop(self):
        """Stop resource monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_resources(self):
        """Monitor system resources in background thread"""
        process = psutil.Process(os.getpid())
        
        while self.monitoring:
            try:
                # Get current resource usage
                memory_info = process.memory_info()
                cpu_percent = process.cpu_percent()
                
                self.metrics.append({
                    'timestamp': time.time() - self.start_time,
                    'memory_mb': memory_info.rss / 1024 / 1024,  # Convert to MB
                    'cpu_percent': cpu_percent
                })
                
                time.sleep(1)  # Sample every second
                
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                break
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get collected resource metrics"""
        if not self.metrics:
            return {}
        
        memory_values = [m['memory_mb'] for m in self.metrics]
        cpu_values = [m['cpu_percent'] for m in self.metrics if m['cpu_percent'] > 0]
        
        return {
            'peak_memory_mb': max(memory_values) if memory_values else 0,
            'average_memory_mb': statistics.mean(memory_values) if memory_values else 0,
            'memory_growth_mb': memory_values[-1] - memory_values[0] if len(memory_values) > 1 else 0,
            'peak_cpu_percent': max(cpu_values) if cpu_values else 0,
            'average_cpu_percent': statistics.mean(cpu_values) if cpu_values else 0,
            'sample_count': len(self.metrics)
        }


async def main():
    """Main function to run performance tests"""
    # Check if backend is available
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:5000/health") as response:
                if response.status != 200:
                    logger.error("Backend service is not available")
                    return False
    except Exception as e:
        logger.error(f"Cannot connect to backend service: {e}")
        return False
    
    # Run performance tests
    test_suite = PerformanceTestSuite()
    results = await test_suite.run_all_performance_tests()
    
    # Print report
    test_suite.print_performance_report(results)
    
    # Save results to file
    with open('performance_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info("Performance test results saved to performance_test_results.json")
    
    # Return success/failure based on overall status
    summary = results.get('summary', {})
    return summary.get('overall_status') == 'PASS'


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)