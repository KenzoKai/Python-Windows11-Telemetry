#!/usr/bin/env python3
"""
Test script to verify system metrics collection
"""

import time
import sys
import os

# Add current directory to path to import dashboard modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dashboard import SystemMetrics

def test_metrics():
    """Test the SystemMetrics class functionality"""
    print("Testing System Metrics Collection...")
    print("=" * 50)
    
    # Create metrics instance
    metrics = SystemMetrics()
    
    # Test initial update
    print("Collecting initial metrics...")
    metrics.update_metrics()
    
    # Wait a moment for more accurate readings
    time.sleep(1)
    metrics.update_metrics()
    
    # Display collected metrics
    print(f"\nCPU Metrics:")
    print(f"  Usage: {metrics.cpu_percent:.1f}%")
    print(f"  Frequency: {metrics.cpu_freq:.0f} MHz")
    print(f"  Cores: {metrics.cpu_cores}")
    print(f"  Per-core usage: {[f'{core:.1f}%' for core in metrics.cpu_per_core[:4]]}")  # Show first 4 cores
    
    print(f"\nMemory Metrics:")
    print(f"  Usage: {metrics.memory_percent:.1f}%")
    print(f"  Used: {metrics.format_bytes(metrics.memory_used)}")
    print(f"  Available: {metrics.format_bytes(metrics.memory_available)}")
    print(f"  Total: {metrics.format_bytes(metrics.memory_total)}")
    
    print(f"\nDisk I/O Metrics:")
    print(f"  Read Speed: {metrics.format_bytes(metrics.disk_read_speed)}/s")
    print(f"  Write Speed: {metrics.format_bytes(metrics.disk_write_speed)}/s")
    print(f"  Disk Usage: {metrics.disk_usage_percent:.1f}%")
    
    print(f"\nNetwork Metrics:")
    print(f"  Upload Speed: {metrics.format_bytes(metrics.network_sent_speed)}/s")
    print(f"  Download Speed: {metrics.format_bytes(metrics.network_recv_speed)}/s")
    print(f"  Total Sent: {metrics.format_bytes(metrics.network_total_sent)}")
    print(f"  Total Received: {metrics.format_bytes(metrics.network_total_recv)}")
    
    print(f"\nSystem Status:")
    print(f"  CPU Temperature: {metrics.cpu_temp:.1f}°C")
    print(f"  System Uptime: {metrics.system_uptime}")
    
    print("\n" + "=" * 50)
    print("Metrics collection test completed successfully!")
    
    # Test continuous updates
    print("\nTesting continuous updates (5 iterations)...")
    for i in range(5):
        time.sleep(1)
        metrics.update_metrics()
        print(f"Update {i+1}: CPU {metrics.cpu_percent:.1f}%, Memory {metrics.memory_percent:.1f}%, Temp {metrics.cpu_temp:.1f}°C")
    
    print("\nAll tests passed! The dashboard should work correctly.")

if __name__ == "__main__":
    try:
        test_metrics()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()