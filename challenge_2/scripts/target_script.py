#!/usr/bin/env python3
"""
Sample Target Script for Challenge 2: Simple Cron Job
Author: Amine Affi
Description: Demonstrates various execution scenarios for testing the cron job system
"""

import os
import sys
import time
import random
import json
import requests
from datetime import datetime
from pathlib import Path


def simulate_data_processing():
    """Simulate some data processing work"""
    print("🔄 Starting data processing simulation...")
    
    # Simulate processing multiple batches
    batch_count = random.randint(3, 8)
    
    for i in range(1, batch_count + 1):
        print(f"📊 Processing batch {i}/{batch_count}")
        
        # Simulate variable processing time
        processing_time = random.uniform(0.5, 2.0)
        time.sleep(processing_time)
        
        # Simulate occasional warnings
        if random.random() < 0.2:  # 20% chance of warning
            print(f"⚠️ WARNING: Slow response detected in batch {i} ({processing_time:.2f}s)")
            
        # Simulate batch completion
        records_processed = random.randint(100, 1000)
        print(f"✅ Batch {i} completed: {records_processed} records processed")
        
    print(f"🎉 Data processing complete! Processed {batch_count} batches successfully")
    return batch_count


def simulate_api_calls():
    """Simulate API interactions"""
    print("\n🌐 Making API calls...")
    
    # List of mock APIs to call
    apis = [
        "https://httpbin.org/delay/1",  # Simulates 1-second delay
        "https://httpbin.org/status/200",  # Always returns 200
        "https://httpbin.org/json",  # Returns JSON data
    ]
    
    successful_calls = 0
    
    for i, api_url in enumerate(apis, 1):
        try:
            print(f"📡 Calling API {i}: {api_url}")
            
            # Make request with timeout
            response = requests.get(api_url, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ API {i} responded successfully (status: {response.status_code})")
                successful_calls += 1
            else:
                print(f"⚠️ WARNING: API {i} returned status {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"❌ ERROR: API {i} timed out")
        except requests.exceptions.RequestException as e:
            print(f"❌ ERROR: API {i} failed: {str(e)}")
        except Exception as e:
            print(f"❌ ERROR: Unexpected error with API {i}: {str(e)}")
            
        # Small delay between calls
        time.sleep(0.5)
        
    print(f"📊 API Summary: {successful_calls}/{len(apis)} calls successful")
    return successful_calls


def simulate_file_operations():
    """Simulate file system operations"""
    print("\n📁 Performing file operations...")
    
    # Create temporary directory
    temp_dir = Path("/tmp/cron_job_test")
    temp_dir.mkdir(exist_ok=True)
    
    operations_completed = 0
    
    try:
        # Create test files
        for i in range(1, 4):
            test_file = temp_dir / f"test_file_{i}.txt"
            
            # Generate some test data
            test_data = {
                "file_id": i,
                "timestamp": datetime.now().isoformat(),
                "data": [random.randint(1, 100) for _ in range(10)],
                "checksum": random.randint(1000, 9999)
            }
            
            with open(test_file, 'w') as f:
                json.dump(test_data, f, indent=2)
                
            print(f"📝 Created {test_file.name} ({test_file.stat().st_size} bytes)")
            operations_completed += 1
            
        # Read and validate files
        for test_file in temp_dir.glob("test_file_*.txt"):
            try:
                with open(test_file, 'r') as f:
                    data = json.load(f)
                print(f"✅ Validated {test_file.name}: checksum {data['checksum']}")
                operations_completed += 1
            except Exception as e:
                print(f"❌ ERROR: Failed to validate {test_file.name}: {e}")
                
        # Cleanup
        for test_file in temp_dir.glob("test_file_*.txt"):
            test_file.unlink()
            operations_completed += 1
            
        temp_dir.rmdir()
        print(f"🧹 Cleanup completed")
        
    except Exception as e:
        print(f"❌ ERROR: File operations failed: {e}")
        return 0
        
    print(f"📊 File Operations Summary: {operations_completed} operations completed")
    return operations_completed


def simulate_memory_usage():
    """Simulate memory-intensive operations"""
    print("\n🧠 Simulating memory usage...")
    
    try:
        # Create some data structures to use memory
        data_size = random.randint(1000, 5000)
        large_list = [random.random() for _ in range(data_size)]
        
        print(f"📈 Allocated list with {len(large_list)} elements")
        
        # Perform some operations on the data
        total = sum(large_list)
        average = total / len(large_list)
        maximum = max(large_list)
        minimum = min(large_list)
        
        print(f"📊 Statistics: avg={average:.4f}, max={maximum:.4f}, min={minimum:.4f}")
        
        # Simulate processing
        time.sleep(1)
        
        # Clean up
        del large_list
        print("🧹 Memory cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Memory operations failed: {e}")
        return False


def generate_execution_summary():
    """Generate a summary of the execution"""
    print("\n📋 EXECUTION SUMMARY")
    print("=" * 50)
    
    summary = {
        "execution_time": datetime.now().isoformat(),
        "script_version": "1.0.0",
        "python_version": sys.version.split()[0],
        "platform": sys.platform,
        "working_directory": str(Path.cwd()),
        "environment_variables": len(os.environ),
        "process_id": os.getpid()
    }
    
    for key, value in summary.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
        
    return summary


def main():
    """Main execution function"""
    print("🚀 Starting Target Script Execution")
    print(f"⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Track overall success
    overall_success = True
    results = {}
    
    try:
        # Run different simulation modules
        results["data_processing"] = simulate_data_processing()
        results["api_calls"] = simulate_api_calls()
        results["file_operations"] = simulate_file_operations()
        results["memory_usage"] = simulate_memory_usage()
        
        # Generate summary
        results["summary"] = generate_execution_summary()
        
        # Simulate occasional failures for testing
        failure_chance = 0.1  # 10% chance of simulated failure
        if random.random() < failure_chance:
            raise Exception("Simulated random failure for testing error handling")
            
    except KeyboardInterrupt:
        print("\n❌ Execution interrupted by user")
        overall_success = False
        sys.exit(130)  # Standard exit code for Ctrl+C
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        overall_success = False
        sys.exit(1)
        
    # Final status
    print("\n" + "=" * 60)
    if overall_success:
        print("✅ TARGET SCRIPT COMPLETED SUCCESSFULLY")
        print(f"📊 Results: {json.dumps(results, indent=2)}")
        sys.exit(0)
    else:
        print("❌ TARGET SCRIPT COMPLETED WITH ERRORS")
        sys.exit(1)


if __name__ == "__main__":
    main()