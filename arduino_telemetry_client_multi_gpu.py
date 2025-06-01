#!/usr/bin/env python3
"""
Arduino Telemetry Client - Multi-GPU Support
Sends system telemetry data to Arduino Giga R1 with Display Shield via WiFi
Supports multiple GPUs and prioritizes discrete NVIDIA GPUs over integrated graphics
"""

import json
import time
import socket
import threading
from datetime import datetime
import psutil
import platform

try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False

try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

try:
    import nvidia_ml_py3 as nvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False

class TelemetryClient:
    """Collects and sends telemetry data to Arduino"""
    
    def __init__(self, arduino_ip="192.168.1.100", arduino_port=8080):
        self.arduino_ip = arduino_ip
        self.arduino_port = arduino_port
        self.running = False
        self.socket = None
        
        # Initialize metrics
        self.prev_disk_read = 0
        self.prev_disk_write = 0
        self.prev_net_sent = 0
        self.prev_net_recv = 0
        self.prev_time = time.time()
        
        # Initialize GPU monitoring
        self.gpu_initialized = False
        self.gpu_available = False
        self.nvidia_gpus = []
        self.all_gpus = []
        self.primary_gpu_method = None
        
        # Try NVML first (NVIDIA GPUs)
        if NVML_AVAILABLE:
            try:
                nvml.nvmlInit()
                device_count = nvml.nvmlDeviceGetCount()
                if device_count > 0:
                    self.gpu_initialized = True
                    self.gpu_available = True
                    self.primary_gpu_method = "NVML"
                    for i in range(device_count):
                        handle = nvml.nvmlDeviceGetHandleByIndex(i)
                        gpu_name = nvml.nvmlDeviceGetName(handle).decode('utf-8')
                        self.nvidia_gpus.append((i, handle, gpu_name))
                        self.all_gpus.append(f"NVIDIA {gpu_name}")
                    print(f"NVML initialized - Found {device_count} NVIDIA GPU(s):")
                    for i, (idx, handle, name) in enumerate(self.nvidia_gpus):
                        print(f"  GPU {idx}: {name}")
                else:
                    print("NVML: No NVIDIA GPUs detected")
            except Exception as e:
                print(f"NVML initialization failed: {e}")
        
        # Try GPUtil for additional GPU detection
        if GPU_AVAILABLE:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    if not self.gpu_available:
                        self.gpu_available = True
                        self.primary_gpu_method = "GPUtil"
                    
                    print(f"GPUtil found {len(gpus)} GPU(s):")
                    for i, gpu in enumerate(gpus):
                        print(f"  GPU {i}: {gpu.name}")
                        if gpu.name not in [g.split(' ', 1)[1] if ' ' in g else g for g in self.all_gpus]:
                            self.all_gpus.append(gpu.name)
                else:
                    print("GPUtil: No GPUs detected")
            except Exception as e:
                print(f"GPUtil error: {e}")
        
        # Try WMI for comprehensive GPU listing
        if WMI_AVAILABLE:
            try:
                import wmi
                w = wmi.WMI()
                wmi_gpus = []
                for gpu in w.Win32_VideoController():
                    if gpu.Name and "Microsoft" not in gpu.Name and "Basic" not in gpu.Name:
                        wmi_gpus.append(gpu.Name)
                        if gpu.Name not in self.all_gpus:
                            self.all_gpus.append(gpu.Name)
                
                if wmi_gpus:
                    print(f"WMI found {len(wmi_gpus)} GPU(s):")
                    for gpu in wmi_gpus:
                        print(f"  {gpu}")
                    
                    if not self.gpu_available:
                        self.gpu_available = True
                        self.primary_gpu_method = "WMI"
                        
            except Exception as e:
                print(f"WMI GPU detection error: {e}")
        
        if self.gpu_available:
            print(f"Primary GPU monitoring method: {self.primary_gpu_method}")
            print(f"Total GPUs detected: {len(self.all_gpus)}")
        else:
            print("No GPU monitoring available - will show estimated values")
        
        print(f"Telemetry Client initialized")
        print(f"Target Arduino: {arduino_ip}:{arduino_port}")
    
    def collect_metrics(self):
        """Collect current system metrics"""
        current_time = time.time()
        time_diff = current_time - self.prev_time
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_freq_info = psutil.cpu_freq()
        cpu_freq = cpu_freq_info.current if cpu_freq_info else 0
        cpu_cores = psutil.cpu_count()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = memory.used / (1024**3)
        memory_total_gb = memory.total / (1024**3)
        
        # Disk metrics
        disk_read_speed = 0
        disk_write_speed = 0
        disk_io = psutil.disk_io_counters()
        if disk_io and time_diff > 0:
            read_diff = disk_io.read_bytes - self.prev_disk_read
            write_diff = disk_io.write_bytes - self.prev_disk_write
            disk_read_speed = (read_diff / time_diff) / (1024**2)  # MB/s
            disk_write_speed = (write_diff / time_diff) / (1024**2)  # MB/s
            self.prev_disk_read = disk_io.read_bytes
            self.prev_disk_write = disk_io.write_bytes
        
        # Disk usage
        disk_usage = psutil.disk_usage('/')
        disk_usage_percent = (disk_usage.used / disk_usage.total) * 100
        
        # Network metrics
        network_sent_speed = 0
        network_recv_speed = 0
        net_io = psutil.net_io_counters()
        if net_io and time_diff > 0:
            sent_diff = net_io.bytes_sent - self.prev_net_sent
            recv_diff = net_io.bytes_recv - self.prev_net_recv
            network_sent_speed = (sent_diff / time_diff) / (1024**2)  # MB/s
            network_recv_speed = (recv_diff / time_diff) / (1024**2)  # MB/s
            self.prev_net_sent = net_io.bytes_sent
            self.prev_net_recv = net_io.bytes_recv
        
        # Temperature (estimated if WMI not available)
        cpu_temp = self.get_cpu_temperature(cpu_percent)
        
        # GPU metrics
        gpu_usage, gpu_memory_percent, gpu_temp, gpu_name = self.get_gpu_metrics()
        
        # System uptime
        boot_time = psutil.boot_time()
        uptime_seconds = current_time - boot_time
        uptime_hours = int(uptime_seconds // 3600)
        uptime_minutes = int((uptime_seconds % 3600) // 60)
        
        self.prev_time = current_time
        
        # Create telemetry packet
        telemetry = {
            "timestamp": datetime.now().isoformat(),
            "cpu": {
                "usage": round(cpu_percent, 1),
                "frequency": round(cpu_freq, 0),
                "cores": cpu_cores,
                "temperature": round(cpu_temp, 1)
            },
            "memory": {
                "usage_percent": round(memory_percent, 1),
                "used_gb": round(memory_used_gb, 1),
                "total_gb": round(memory_total_gb, 1)
            },
            "disk": {
                "read_speed": round(disk_read_speed, 1),
                "write_speed": round(disk_write_speed, 1),
                "usage_percent": round(disk_usage_percent, 1)
            },
            "network": {
                "upload_speed": round(network_sent_speed, 1),
                "download_speed": round(network_recv_speed, 1)
            },
            "gpu": {
                "usage": round(gpu_usage, 1),
                "memory_percent": round(gpu_memory_percent, 1),
                "temperature": round(gpu_temp, 1),
                "name": gpu_name[:20]  # Truncate for display
            },
            "system": {
                "uptime_hours": uptime_hours,
                "uptime_minutes": uptime_minutes,
                "platform": platform.system()
            }
        }
        
        return telemetry
    
    def get_cpu_temperature(self, cpu_percent):
        """Get CPU temperature (estimated if sensors not available)"""
        if WMI_AVAILABLE:
            try:
                w = wmi.WMI(namespace="root\\OpenHardwareMonitor")
                for sensor in w.Win32_TemperatureProbe():
                    if sensor.CurrentReading:
                        temp_celsius = (sensor.CurrentReading / 10.0) - 273.15
                        if 0 < temp_celsius < 150:
                            return temp_celsius
            except:
                pass
        
        # Fallback: estimate based on CPU usage
        base_temp = 35
        load_factor = cpu_percent / 100.0
        return base_temp + (load_factor * 30)
    
    def get_gpu_metrics(self):
        """Get GPU metrics - prioritizes discrete NVIDIA GPUs over integrated graphics"""
        gpu_usage = 0
        gpu_memory_percent = 0
        gpu_temp = 0
        gpu_name = "No GPU"
        
        # Priority 1: NVIDIA GPUs via NVML (RTX 3090 should be detected here)
        if self.gpu_initialized and NVML_AVAILABLE and self.nvidia_gpus:
            try:
                # Find the most powerful NVIDIA GPU (usually RTX 3090)
                primary_gpu = self.nvidia_gpus[0]  # Start with first
                for idx, handle, name in self.nvidia_gpus:
                    if "RTX" in name or "GTX" in name or "3090" in name:
                        primary_gpu = (idx, handle, name)
                        break
                
                idx, handle, name = primary_gpu
                
                # Get utilization
                util = nvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_usage = util.gpu
                
                # Get memory info
                mem_info = nvml.nvmlDeviceGetMemoryInfo(handle)
                gpu_memory_percent = (mem_info.used / mem_info.total) * 100
                
                # Get temperature
                try:
                    gpu_temp = nvml.nvmlDeviceGetTemperature(handle, nvml.NVML_TEMPERATURE_GPU)
                except:
                    gpu_temp = 45  # Fallback temperature
                
                gpu_name = name
                
                print(f"NVML GPU {idx} ({name}): {gpu_usage}% usage, {gpu_memory_percent:.1f}% memory, {gpu_temp}°C")
                return gpu_usage, gpu_memory_percent, gpu_temp, gpu_name
                
            except Exception as e:
                print(f"NVML error: {e}")
        
        # Priority 2: GPUtil - look for discrete GPUs first
        if GPU_AVAILABLE:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    # Prioritize discrete GPUs over integrated
                    discrete_gpu = None
                    for gpu in gpus:
                        if gpu.name and ("RTX" in gpu.name or "GTX" in gpu.name or "3090" in gpu.name or 
                                       "RX" in gpu.name or gpu.memoryTotal > 4000):  # >4GB likely discrete
                            discrete_gpu = gpu
                            break
                    
                    # Use discrete GPU if found, otherwise first GPU
                    target_gpu = discrete_gpu if discrete_gpu else gpus[0]
                    
                    gpu_usage = target_gpu.load * 100 if target_gpu.load is not None else 0
                    gpu_memory_percent = (target_gpu.memoryUsed / target_gpu.memoryTotal) * 100 if target_gpu.memoryTotal > 0 else 0
                    gpu_temp = target_gpu.temperature if target_gpu.temperature is not None else 45
                    gpu_name = target_gpu.name if target_gpu.name else "Unknown GPU"
                    
                    print(f"GPUtil GPU ({gpu_name}): {gpu_usage}% usage, {gpu_memory_percent:.1f}% memory, {gpu_temp}°C")
                    return gpu_usage, gpu_memory_percent, gpu_temp, gpu_name
                    
            except Exception as e:
                print(f"GPUtil error: {e}")
        
        # Priority 3: WMI - prioritize discrete GPUs
        try:
            if WMI_AVAILABLE:
                import wmi
                w = wmi.WMI()
                discrete_gpus = []
                integrated_gpus = []
                
                for gpu in w.Win32_VideoController():
                    if gpu.Name and "Microsoft" not in gpu.Name and "Basic" not in gpu.Name:
                        # Categorize GPUs
                        if ("RTX" in gpu.Name or "GTX" in gpu.Name or "3090" in gpu.Name or 
                            "RX" in gpu.Name or "Radeon" in gpu.Name):
                            if "RTX" in gpu.Name or "GTX" in gpu.Name or "3090" in gpu.Name:
                                discrete_gpus.insert(0, gpu)  # NVIDIA first
                            else:
                                discrete_gpus.append(gpu)
                        else:
                            integrated_gpus.append(gpu)
                
                # Use discrete GPU if available, prefer NVIDIA
                target_gpu = None
                if discrete_gpus:
                    target_gpu = discrete_gpus[0]
                elif integrated_gpus:
                    target_gpu = integrated_gpus[0]
                
                if target_gpu:
                    gpu_name = target_gpu.Name[:20]
                    
                    # Estimate GPU usage based on CPU usage
                    cpu_percent = psutil.cpu_percent(interval=None)
                    
                    # Better estimation for discrete vs integrated
                    if "RTX" in gpu_name or "GTX" in gpu_name or "3090" in gpu_name:
                        gpu_usage = min(cpu_percent * 0.8, 100)  # Discrete NVIDIA
                        gpu_memory_percent = 30
                        gpu_temp = 50 + (gpu_usage * 0.4)
                    elif "RX" in gpu_name or "Radeon" in gpu_name:
                        gpu_usage = min(cpu_percent * 0.7, 100)  # Discrete AMD
                        gpu_memory_percent = 25
                        gpu_temp = 45 + (gpu_usage * 0.3)
                    else:
                        gpu_usage = min(cpu_percent * 0.4, 100)  # Integrated
                        gpu_memory_percent = 15
                        gpu_temp = 40 + (gpu_usage * 0.2)
                    
                    print(f"WMI GPU ({gpu_name}): {gpu_usage:.1f}% usage, {gpu_memory_percent}% memory, {gpu_temp:.1f}°C")
                    return gpu_usage, gpu_memory_percent, gpu_temp, gpu_name
                        
        except Exception as e:
            print(f"WMI GPU fallback error: {e}")
        
        # Final fallback - provide some realistic test values
        if gpu_name == "No GPU":
            gpu_name = "Integrated Graphics"
            cpu_percent = psutil.cpu_percent(interval=None)
            gpu_usage = min(cpu_percent * 0.4, 100)  # Light GPU usage estimate
            gpu_memory_percent = 15  # Low memory usage
            gpu_temp = 40 + (gpu_usage * 0.2)  # Conservative temperature
            
            print(f"Fallback GPU (estimated): {gpu_usage:.1f}% usage, {gpu_memory_percent}% memory, {gpu_temp:.1f}°C")
        
        return gpu_usage, gpu_memory_percent, gpu_temp, gpu_name
    
    def connect_to_arduino(self):
        """Establish connection to Arduino"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)
            self.socket.connect((self.arduino_ip, self.arduino_port))
            print(f"Connected to Arduino at {self.arduino_ip}:{self.arduino_port}")
            return True
        except Exception as e:
            print(f"Failed to connect to Arduino: {e}")
            return False
    
    def send_telemetry(self, telemetry):
        """Send telemetry data to Arduino"""
        try:
            # Convert to JSON and add newline for Arduino parsing
            json_data = json.dumps(telemetry) + "\n"
            self.socket.send(json_data.encode('utf-8'))
            return True
        except Exception as e:
            print(f"Failed to send telemetry: {e}")
            return False
    
    def run(self, update_interval=2.0):
        """Main loop to collect and send telemetry"""
        self.running = True
        
        while self.running:
            try:
                # Connect if not connected
                if not self.socket:
                    if not self.connect_to_arduino():
                        time.sleep(5)  # Wait before retry
                        continue
                
                # Collect and send telemetry
                telemetry = self.collect_metrics()
                
                if self.send_telemetry(telemetry):
                    print(f"Sent: CPU {telemetry['cpu']['usage']}%, "
                          f"Memory {telemetry['memory']['usage_percent']}%, "
                          f"GPU {telemetry['gpu']['usage']}% ({telemetry['gpu']['name']}), "
                          f"GPU Temp {telemetry['gpu']['temperature']}°C")
                else:
                    # Connection lost, reset socket
                    self.socket.close()
                    self.socket = None
                
                time.sleep(update_interval)
                
            except KeyboardInterrupt:
                print("\nStopping telemetry client...")
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                if self.socket:
                    self.socket.close()
                    self.socket = None
                time.sleep(5)
        
        self.running = False
        if self.socket:
            self.socket.close()

def main():
    """Main entry point"""
    print("Arduino Telemetry Client - Multi-GPU Support")
    print("=============================================")
    
    # Get Arduino IP from user
    arduino_ip = input("Enter Arduino IP address (default: 192.168.1.100): ").strip()
    if not arduino_ip:
        arduino_ip = "192.168.1.100"
    
    arduino_port = 8080
    
    try:
        client = TelemetryClient(arduino_ip, arduino_port)
        client.run(update_interval=2.0)  # Send every 2 seconds
    except KeyboardInterrupt:
        print("\nClient stopped by user")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()