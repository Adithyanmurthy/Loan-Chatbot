#!/usr/bin/env python3
"""
Integration Test Startup Script
Starts all required services and runs end-to-end integration tests
Based on task 15.1: Integrate all components and test complete workflows
"""

import subprocess
import time
import sys
import os
import signal
import requests
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntegrationTestRunner:
    """Manages the startup and coordination of all services for integration testing"""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.services = {
            'mock_apis': {
                'command': ['node', 'server.js'],
                'cwd': 'mock-apis',
                'health_checks': [
                    'http://localhost:3001/health',
                    'http://localhost:3002/health', 
                    'http://localhost:3003/health'
                ],
                'startup_delay': 5
            },
            'backend': {
                'command': [sys.executable, 'app.py'],
                'cwd': 'backend',
                'health_checks': ['http://localhost:5000/health'],
                'startup_delay': 10
            }
        }
        
    def start_service(self, service_name: str, config: Dict[str, Any]) -> subprocess.Popen:
        """Start a single service"""
        logger.info(f"Starting {service_name}...")
        
        try:
            # Change to service directory
            original_cwd = os.getcwd()
            if config.get('cwd'):
                os.chdir(config['cwd'])
            
            # Start the process
            process = subprocess.Popen(
                config['command'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Return to original directory
            os.chdir(original_cwd)
            
            self.processes.append(process)
            logger.info(f"✓ {service_name} started with PID {process.pid}")
            
            return process
            
        except Exception as e:
            logger.error(f"✗ Failed to start {service_name}: {e}")
            raise
    
    def wait_for_service_health(self, service_name: str, health_urls: List[str], timeout: int = 60) -> bool:
        """Wait for service to become healthy"""
        logger.info(f"Waiting for {service_name} to become healthy...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            all_healthy = True
            
            for url in health_urls:
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code != 200:
                        all_healthy = False
                        break
                except Exception:
                    all_healthy = False
                    break
            
            if all_healthy:
                logger.info(f"✓ {service_name} is healthy")
                return True
            
            time.sleep(2)
        
        logger.error(f"✗ {service_name} failed to become healthy within {timeout} seconds")
        return False
    
    def start_all_services(self) -> bool:
        """Start all required services"""
        logger.info("Starting all services for integration testing...")
        
        for service_name, config in self.services.items():
            try:
                # Start the service
                process = self.start_service(service_name, config)
                
                # Wait for startup delay
                startup_delay = config.get('startup_delay', 5)
                logger.info(f"Waiting {startup_delay} seconds for {service_name} to initialize...")
                time.sleep(startup_delay)
                
                # Check if process is still running
                if process.poll() is not None:
                    stdout, stderr = process.communicate()
                    logger.error(f"✗ {service_name} exited early:")
                    logger.error(f"STDOUT: {stdout}")
                    logger.error(f"STDERR: {stderr}")
                    return False
                
                # Wait for health checks
                health_urls = config.get('health_checks', [])
                if health_urls:
                    if not self.wait_for_service_health(service_name, health_urls):
                        return False
                
            except Exception as e:
                logger.error(f"Failed to start {service_name}: {e}")
                return False
        
        logger.info("✓ All services started successfully")
        return True
    
    def run_integration_tests(self) -> bool:
        """Run the integration test suite"""
        logger.info("Running integration test suite...")
        
        try:
            # Run the integration tests
            result = subprocess.run([
                sys.executable, 'backend/test_e2e_integration.py'
            ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
            
            # Print test output
            if result.stdout:
                logger.info("Test Output:")
                print(result.stdout)
            
            if result.stderr:
                logger.error("Test Errors:")
                print(result.stderr)
            
            if result.returncode == 0:
                logger.info("✓ Integration tests PASSED")
                return True
            else:
                logger.error(f"✗ Integration tests FAILED (exit code: {result.returncode})")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("✗ Integration tests timed out")
            return False
        except Exception as e:
            logger.error(f"✗ Failed to run integration tests: {e}")
            return False
    
    def stop_all_services(self):
        """Stop all running services"""
        logger.info("Stopping all services...")
        
        for process in self.processes:
            try:
                if process.poll() is None:  # Process is still running
                    logger.info(f"Stopping process {process.pid}...")
                    process.terminate()
                    
                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=10)
                        logger.info(f"✓ Process {process.pid} stopped gracefully")
                    except subprocess.TimeoutExpired:
                        logger.warning(f"Process {process.pid} didn't stop gracefully, killing...")
                        process.kill()
                        process.wait()
                        logger.info(f"✓ Process {process.pid} killed")
                        
            except Exception as e:
                logger.error(f"Error stopping process {process.pid}: {e}")
        
        self.processes.clear()
        logger.info("✓ All services stopped")
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are available"""
        logger.info("Checking prerequisites...")
        
        # Check Python
        try:
            python_version = sys.version_info
            if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
                logger.error("Python 3.8+ is required")
                return False
            logger.info(f"✓ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        except Exception as e:
            logger.error(f"Python check failed: {e}")
            return False
        
        # Check Node.js
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✓ Node.js {result.stdout.strip()}")
            else:
                logger.error("Node.js is not available")
                return False
        except Exception as e:
            logger.error(f"Node.js check failed: {e}")
            return False
        
        # Check required directories
        required_dirs = ['backend', 'mock-apis', 'frontend']
        for dir_name in required_dirs:
            if not os.path.isdir(dir_name):
                logger.error(f"Required directory not found: {dir_name}")
                return False
            logger.info(f"✓ Directory {dir_name} exists")
        
        # Check required files
        required_files = [
            'backend/app.py',
            'backend/test_e2e_integration.py',
            'mock-apis/server.js'
        ]
        for file_path in required_files:
            if not os.path.isfile(file_path):
                logger.error(f"Required file not found: {file_path}")
                return False
            logger.info(f"✓ File {file_path} exists")
        
        logger.info("✓ All prerequisites satisfied")
        return True
    
    def run_complete_integration_test(self) -> bool:
        """Run the complete integration test workflow"""
        logger.info("="*60)
        logger.info("AI LOAN CHATBOT - INTEGRATION TEST SUITE")
        logger.info("="*60)
        
        try:
            # Check prerequisites
            if not self.check_prerequisites():
                logger.error("Prerequisites check failed")
                return False
            
            # Start all services
            if not self.start_all_services():
                logger.error("Failed to start services")
                return False
            
            # Run integration tests
            test_success = self.run_integration_tests()
            
            return test_success
            
        except KeyboardInterrupt:
            logger.info("Integration test interrupted by user")
            return False
        except Exception as e:
            logger.error(f"Integration test failed with exception: {e}")
            return False
        finally:
            # Always stop services
            self.stop_all_services()


def signal_handler(signum, frame):
    """Handle interrupt signals"""
    logger.info("Received interrupt signal, shutting down...")
    sys.exit(1)


def main():
    """Main function"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run integration tests
    runner = IntegrationTestRunner()
    success = runner.run_complete_integration_test()
    
    if success:
        logger.info("🎉 Integration tests completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Integration tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()