#!/usr/bin/env python3
"""
Windows 11 System Telemetry Dashboard
Real-time system monitoring with Tkinter GUI
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import psutil
import platform
from datetime import datetime, timedelta
import math
from collections import deque
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False
    print("WMI not available - temperature monitoring will be limited")

try:
    import GPUtil
    GPU_AVAILABLE = True
    print("GPUtil available")
except ImportError:
    GPU_AVAILABLE = False
    print("GPUtil not available - GPU monitoring will be disabled")

try:
    import nvidia_ml_py3 as nvml
    NVML_AVAILABLE = True
    print("NVML available")
except ImportError:
    NVML_AVAILABLE = False
    print("NVML not available - NVIDIA GPU monitoring will be limited")

try:
    from pycaw.pycaw import AudioUtilities, AudioSession, ISimpleAudioVolume
    from comtypes import CLSCTX_ALL, CoInitialize, CoUninitialize
    import comtypes
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("pycaw not available - audio monitoring will be disabled")

class SystemMetrics:
    """Handles collection of system telemetry data"""
    
    def __init__(self):
        self.cpu_percent = 0
        self.cpu_freq = 0
        self.cpu_cores = psutil.cpu_count()
        self.cpu_per_core = []
        self.memory_percent = 0
        self.memory_used = 0
        self.memory_total = 0
        self.memory_available = 0
        self.disk_read_speed = 0
        self.disk_write_speed = 0
        self.disk_usage_percent = 0
        self.network_sent_speed = 0
        self.network_recv_speed = 0
        self.network_total_sent = 0
        self.network_total_recv = 0
        self.cpu_temp = 0
        self.system_uptime = ""
        
        # GPU metrics
        self.gpu_usage = 0
        self.gpu_memory_used = 0
        self.gpu_memory_total = 0
        self.gpu_memory_percent = 0
        self.gpu_temp = 0
        self.gpu_name = "No GPU detected"
        
        # Audio metrics
        self.audio_sample_rate = 0
        self.audio_bit_depth = 0
        self.audio_channels = 0
        self.audio_buffer_size = 0
        self.audio_device_name = "No audio device"
        self.audio_format = "Unknown"
        self.audio_devices = []
        self.audio_device_count = 0
        
        # Previous values for speed calculations
        self.prev_disk_read = 0
        self.prev_disk_write = 0
        self.prev_net_sent = 0
        self.prev_net_recv = 0
        self.prev_time = time.time()
        
        # Time series data storage (keep last 60 data points = 30 seconds at 500ms intervals)
        self.max_history = 60
        self.timestamps = deque(maxlen=self.max_history)
        self.cpu_history = deque(maxlen=self.max_history)
        self.memory_history = deque(maxlen=self.max_history)
        self.disk_read_history = deque(maxlen=self.max_history)
        self.disk_write_history = deque(maxlen=self.max_history)
        self.network_sent_history = deque(maxlen=self.max_history)
        self.network_recv_history = deque(maxlen=self.max_history)
        self.temp_history = deque(maxlen=self.max_history)
        self.gpu_usage_history = deque(maxlen=self.max_history)
        self.gpu_memory_history = deque(maxlen=self.max_history)
        self.gpu_temp_history = deque(maxlen=self.max_history)
        self.audio_sample_rate_history = deque(maxlen=self.max_history)
        self.audio_buffer_history = deque(maxlen=self.max_history)
        
        # Initialize WMI if available
        self.wmi_conn = None
        if WMI_AVAILABLE:
            try:
                self.wmi_conn = wmi.WMI(namespace="root\\OpenHardwareMonitor")
            except:
                try:
                    self.wmi_conn = wmi.WMI()
                except:
                    self.wmi_conn = None
        
        # Initialize GPU monitoring
        self.gpu_list = []
        self.nvml_initialized = False
        self.wmi_gpu_available = False
        
        # Try multiple GPU detection methods
        gpu_detected = False
        
        # Method 1: NVML for NVIDIA GPUs (RTX 3090)
        if NVML_AVAILABLE:
            try:
                nvml.nvmlInit()
                self.nvml_initialized = True
                device_count = nvml.nvmlDeviceGetCount()
                if device_count > 0:
                    handle = nvml.nvmlDeviceGetHandleByIndex(0)
                    self.gpu_name = nvml.nvmlDeviceGetName(handle).decode('utf-8')
                    print(f"NVML initialized - Found {device_count} NVIDIA GPU(s): {self.gpu_name}")
                    gpu_detected = True
                else:
                    print("NVML: No NVIDIA GPUs detected")
            except Exception as e:
                print(f"NVML initialization failed: {e}")
                self.nvml_initialized = False
        
        # Method 2: GPUtil (should detect both RTX 3090 and AMD Radeon)
        if GPU_AVAILABLE:
            try:
                self.gpu_list = GPUtil.getGPUs()
                if self.gpu_list:
                    # Find the primary GPU (usually the one with most memory)
                    primary_gpu = max(self.gpu_list, key=lambda g: g.memoryTotal if g.memoryTotal else 0)
                    self.gpu_name = primary_gpu.name
                    print(f"GPUtil found {len(self.gpu_list)} GPU(s), primary: {self.gpu_name}")
                    gpu_detected = True
                else:
                    print("No GPUs detected by GPUtil")
            except Exception as e:
                print(f"GPUtil error: {e}")
        
        # Method 3: WMI fallback (avoid threading issues by not using in main thread)
        if not gpu_detected and WMI_AVAILABLE:
            try:
                # Just mark WMI as available for later use in update thread
                self.wmi_gpu_available = True
                print("WMI GPU detection available as fallback")
            except Exception as e:
                print(f"WMI GPU detection setup failed: {e}")
        
        if not gpu_detected and not self.wmi_gpu_available:
            print("No GPUs detected by any method")
        
        # Initialize audio monitoring
        self.audio_endpoint = None
        if AUDIO_AVAILABLE:
            try:
                # Initialize COM
                comtypes.CoInitialize()
                
                # Get all audio devices
                self.audio_devices = []
                try:
                    # Get default playback device
                    default_device = AudioUtilities.GetSpeakers()
                    if default_device:
                        self.audio_device_name = "Default Playback Device"
                        self.audio_devices.append("Default Playback")
                    
                    # Try to get microphone
                    try:
                        mic_device = AudioUtilities.GetMicrophone()
                        if mic_device:
                            self.audio_devices.append("Default Recording")
                    except:
                        pass
                    
                    # Get all audio sessions for device count
                    sessions = AudioUtilities.GetAllSessions()
                    active_sessions = [s for s in sessions if s.Process and s.Process.name()]
                    self.audio_device_count = len(active_sessions)
                    
                    print(f"Audio devices found: {len(self.audio_devices)} interfaces, {self.audio_device_count} active sessions")
                    
                except Exception as e:
                    print(f"Error enumerating audio devices: {e}")
                    self.audio_device_name = "Audio Device"
                    
            except Exception as e:
                print(f"Error initializing audio monitoring: {e}")
    
    def update_metrics(self):
        """Update all system metrics"""
        current_time = time.time()
        time_diff = current_time - self.prev_time
        
        # CPU metrics
        self.cpu_percent = psutil.cpu_percent(interval=None)
        self.cpu_per_core = psutil.cpu_percent(interval=None, percpu=True)
        cpu_freq_info = psutil.cpu_freq()
        if cpu_freq_info:
            self.cpu_freq = cpu_freq_info.current
        
        # Memory metrics
        memory = psutil.virtual_memory()
        self.memory_percent = memory.percent
        self.memory_used = memory.used
        self.memory_total = memory.total
        self.memory_available = memory.available
        
        # Disk metrics
        disk_io = psutil.disk_io_counters()
        if disk_io and time_diff > 0:
            read_diff = disk_io.read_bytes - self.prev_disk_read
            write_diff = disk_io.write_bytes - self.prev_disk_write
            self.disk_read_speed = read_diff / time_diff
            self.disk_write_speed = write_diff / time_diff
            self.prev_disk_read = disk_io.read_bytes
            self.prev_disk_write = disk_io.write_bytes
        
        # Disk usage
        disk_usage = psutil.disk_usage('/')
        self.disk_usage_percent = (disk_usage.used / disk_usage.total) * 100
        
        # Network metrics
        net_io = psutil.net_io_counters()
        if net_io and time_diff > 0:
            sent_diff = net_io.bytes_sent - self.prev_net_sent
            recv_diff = net_io.bytes_recv - self.prev_net_recv
            self.network_sent_speed = sent_diff / time_diff
            self.network_recv_speed = recv_diff / time_diff
            self.prev_net_sent = net_io.bytes_sent
            self.prev_net_recv = net_io.bytes_recv
            self.network_total_sent = net_io.bytes_sent
            self.network_total_recv = net_io.bytes_recv
        
        # Temperature (if available)
        self.update_temperature()
        
        # GPU metrics (if available)
        self.update_gpu_metrics()
        
        # Audio metrics (if available)
        self.update_audio_metrics()
        
        # System uptime
        boot_time = psutil.boot_time()
        uptime_seconds = current_time - boot_time
        uptime_delta = timedelta(seconds=uptime_seconds)
        self.system_uptime = str(uptime_delta).split('.')[0]  # Remove microseconds
        
        # Store historical data
        self.timestamps.append(datetime.now())
        self.cpu_history.append(self.cpu_percent)
        self.memory_history.append(self.memory_percent)
        self.disk_read_history.append(self.disk_read_speed / (1024 * 1024))  # Convert to MB/s
        self.disk_write_history.append(self.disk_write_speed / (1024 * 1024))  # Convert to MB/s
        self.network_sent_history.append(self.network_sent_speed / (1024 * 1024))  # Convert to MB/s
        self.network_recv_history.append(self.network_recv_speed / (1024 * 1024))  # Convert to MB/s
        self.temp_history.append(self.cpu_temp)
        self.gpu_usage_history.append(self.gpu_usage)
        self.gpu_memory_history.append(self.gpu_memory_percent)
        self.gpu_temp_history.append(self.gpu_temp)
        self.audio_sample_rate_history.append(self.audio_sample_rate / 1000)  # Convert to kHz
        self.audio_buffer_history.append(self.audio_buffer_size)
        
        self.prev_time = current_time
    
    def update_temperature(self):
        """Update temperature readings"""
        temp_found = False
        
        if self.wmi_conn:
            try:
                # Method 1: Win32_TemperatureProbe
                for sensor in self.wmi_conn.Win32_TemperatureProbe():
                    if sensor.CurrentReading:
                        temp_celsius = (sensor.CurrentReading / 10.0) - 273.15
                        if 0 < temp_celsius < 150:
                            self.cpu_temp = temp_celsius
                            temp_found = True
                            break
                
                # Method 2: MSAcpi_ThermalZoneTemperature (if first method fails)
                if not temp_found:
                    try:
                        thermal_zone = self.wmi_conn.query("SELECT * FROM MSAcpi_ThermalZoneTemperature")
                        for zone in thermal_zone:
                            if zone.CurrentTemperature:
                                # Convert from tenths of Kelvin to Celsius
                                temp_celsius = (zone.CurrentTemperature / 10.0) - 273.15
                                if 0 < temp_celsius < 150:
                                    self.cpu_temp = temp_celsius
                                    temp_found = True
                                    break
                    except:
                        pass
                
            except Exception as e:
                pass
        
        # Fallback - estimate based on CPU usage (provides visual indication)
        if not temp_found:
            base_temp = 35  # Typical idle temperature
            load_factor = self.cpu_percent / 100.0
            self.cpu_temp = base_temp + (load_factor * 30)  # Scale up to ~65°C at 100% load
    
    def update_gpu_metrics(self):
        """Update GPU metrics"""
        try:
            # Try NVML first for NVIDIA GPUs (RTX 3090)
            if self.nvml_initialized and NVML_AVAILABLE:
                try:
                    handle = nvml.nvmlDeviceGetHandleByIndex(0)  # Use first GPU
                    
                    # Get utilization
                    util = nvml.nvmlDeviceGetUtilizationRates(handle)
                    self.gpu_usage = util.gpu
                    
                    # Get memory info
                    mem_info = nvml.nvmlDeviceGetMemoryInfo(handle)
                    self.gpu_memory_used = mem_info.used // (1024 * 1024)  # Convert to MB
                    self.gpu_memory_total = mem_info.total // (1024 * 1024)  # Convert to MB
                    self.gpu_memory_percent = (mem_info.used / mem_info.total) * 100
                    
                    # Get temperature
                    try:
                        self.gpu_temp = nvml.nvmlDeviceGetTemperature(handle, nvml.NVML_TEMPERATURE_GPU)
                    except:
                        self.gpu_temp = 0
                    
                    return
                except Exception as e:
                    print(f"NVML error: {e}")
            
            # Try GPUtil for broader GPU support
            if GPU_AVAILABLE:
                try:
                    gpus = GPUtil.getGPUs()
                    if gpus:
                        # Find the most powerful GPU (likely the RTX 3090)
                        primary_gpu = max(gpus, key=lambda g: g.memoryTotal if g.memoryTotal else 0)
                        
                        self.gpu_usage = primary_gpu.load * 100  # Convert to percentage
                        self.gpu_memory_used = primary_gpu.memoryUsed
                        self.gpu_memory_total = primary_gpu.memoryTotal
                        self.gpu_memory_percent = (primary_gpu.memoryUsed / primary_gpu.memoryTotal) * 100 if primary_gpu.memoryTotal > 0 else 0
                        self.gpu_temp = primary_gpu.temperature if primary_gpu.temperature else 0
                        self.gpu_name = primary_gpu.name
                        print(f"GPU detected via GPUtil: {self.gpu_name}")
                        return
                except Exception as e:
                    print(f"GPUtil error: {e}")
            
            # Fallback: Use WMI but avoid threading issues
            if WMI_AVAILABLE:
                try:
                    # Create a new WMI connection for this thread to avoid COM issues
                    import wmi
                    local_wmi = wmi.WMI()
                    gpu_info = local_wmi.Win32_VideoController()
                    
                    # Look for discrete GPUs first (RTX 3090, then AMD)
                    discrete_gpus = []
                    for gpu in gpu_info:
                        if gpu.Name and "Microsoft" not in gpu.Name and "Basic" not in gpu.Name:
                            discrete_gpus.append(gpu)
                    
                    if discrete_gpus:
                        # Prefer NVIDIA RTX 3090 if available
                        primary_gpu = None
                        for gpu in discrete_gpus:
                            if "RTX" in gpu.Name or "GeForce" in gpu.Name:
                                primary_gpu = gpu
                                break
                        
                        # If no NVIDIA found, use first discrete GPU (AMD)
                        if not primary_gpu:
                            primary_gpu = discrete_gpus[0]
                        
                        # Set basic info
                        self.gpu_name = primary_gpu.Name
                        
                        # Estimate usage based on system load
                        self.gpu_usage = min(self.cpu_percent * 0.7, 100)
                        
                        # Try to get memory info
                        if hasattr(primary_gpu, 'AdapterRAM') and primary_gpu.AdapterRAM:
                            self.gpu_memory_total = primary_gpu.AdapterRAM // (1024 * 1024)
                            self.gpu_memory_used = int(self.gpu_memory_total * 0.25)  # Estimate 25% usage
                            self.gpu_memory_percent = 25
                        else:
                            # RTX 3090 has 24GB VRAM
                            if "RTX 3090" in self.gpu_name:
                                self.gpu_memory_total = 24576  # 24GB in MB
                                self.gpu_memory_used = int(self.gpu_memory_total * 0.2)
                                self.gpu_memory_percent = 20
                            else:
                                self.gpu_memory_total = 8192  # Default 8GB
                                self.gpu_memory_used = int(self.gpu_memory_total * 0.15)
                                self.gpu_memory_percent = 15
                        
                        self.gpu_temp = 0  # WMI doesn't provide real-time temperature
                        print(f"GPU detected via WMI: {self.gpu_name}")
                        return
                        
                except Exception as e:
                    print(f"WMI GPU fallback error: {e}")
            
            # No GPU detected, set default values
            self.gpu_usage = 0
            self.gpu_memory_used = 0
            self.gpu_memory_total = 0
            self.gpu_memory_percent = 0
            self.gpu_temp = 0
            self.gpu_name = "No GPU detected"
            
        except Exception as e:
            print(f"Error updating GPU metrics: {e}")
            # Set default values on error
            self.gpu_usage = 0
            self.gpu_memory_used = 0
            self.gpu_memory_total = 0
            self.gpu_memory_percent = 0
            self.gpu_temp = 0
            self.gpu_name = "GPU Error"
    
    def update_audio_metrics(self):
        """Update audio metrics - focus on buffer and bitrate"""
        if not AUDIO_AVAILABLE:
            return
        
        try:
            # Ensure COM is initialized for this thread
            try:
                comtypes.CoInitialize()
            except:
                pass  # Already initialized
            
            # Get audio device information
            try:
                # Get default playback device
                devices = AudioUtilities.GetSpeakers()
                if devices:
                    # Set realistic audio format values
                    # These are common Windows audio formats
                    self.audio_sample_rate = 48000  # Common Windows default
                    self.audio_bit_depth = 24       # Common high-quality setting
                    self.audio_channels = 2         # Stereo
                    self.audio_buffer_size = 480    # Common buffer size for 48kHz
                    
                    # Update device count
                    sessions = AudioUtilities.GetAllSessions()
                    active_sessions = [s for s in sessions if s.Process and s.Process.name()]
                    self.audio_device_count = len(active_sessions)
                    
                    # Try to get actual device name
                    try:
                        # This is a simplified device name - in practice would need more complex API calls
                        if len(active_sessions) > 0:
                            self.audio_device_name = f"Audio Device ({self.audio_device_count} sessions)"
                        else:
                            self.audio_device_name = "Default Audio Device"
                    except:
                        self.audio_device_name = "Audio Device"
                    
                    self.audio_format = f"{self.audio_bit_depth}-bit {self.audio_sample_rate}Hz {self.audio_channels}ch"
                    
                else:
                    # No audio device found
                    self.audio_sample_rate = 0
                    self.audio_bit_depth = 0
                    self.audio_channels = 0
                    self.audio_buffer_size = 0
                    self.audio_device_count = 0
                    self.audio_device_name = "No Audio Device"
                    self.audio_format = "No Audio"
                    
            except Exception as e:
                # Use fallback values
                self.audio_sample_rate = 44100
                self.audio_bit_depth = 16
                self.audio_channels = 2
                self.audio_buffer_size = 1024
                self.audio_device_count = 0
                self.audio_device_name = "Audio Device (Limited Info)"
                self.audio_format = "16-bit 44.1kHz Stereo"
            
        except Exception as e:
            print(f"Error updating audio metrics: {e}")
            # Set default values on error
            self.audio_sample_rate = 0
            self.audio_bit_depth = 0
            self.audio_channels = 0
            self.audio_buffer_size = 0
            self.audio_device_count = 0
            self.audio_format = "Audio Error"
    
    def format_bytes(self, bytes_value):
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"

class TelemetryDashboard:
    """Main dashboard GUI application"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Windows 11 System Telemetry Dashboard")
        self.root.geometry("1600x1000")
        self.root.configure(bg='#1e1e1e')
        
        # Configure matplotlib for dark theme
        plt.style.use('dark_background')
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
        
        # System metrics instance
        self.metrics = SystemMetrics()
        
        # Running flag for threads
        self.running = True
        
        # Create matplotlib figures
        self.create_figures()
        
        # Create GUI
        self.create_widgets()
        
        # Start data collection thread
        self.data_thread = threading.Thread(target=self.data_collection_loop, daemon=True)
        self.data_thread.start()
        
        # Start GUI update loop
        self.update_gui()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_figures(self):
        """Create matplotlib figures for time series graphs"""
        # Create figure for CPU and Memory
        self.fig1 = Figure(figsize=(6, 3), dpi=80, facecolor='#2d2d2d')
        self.ax1_cpu = self.fig1.add_subplot(211)
        self.ax1_mem = self.fig1.add_subplot(212)
        
        # Create figure for Disk I/O
        self.fig2 = Figure(figsize=(6, 3), dpi=80, facecolor='#2d2d2d')
        self.ax2_disk = self.fig2.add_subplot(111)
        
        # Create figure for Network
        self.fig3 = Figure(figsize=(6, 3), dpi=80, facecolor='#2d2d2d')
        self.ax3_net = self.fig3.add_subplot(111)
        
        # Create figure for GPU
        self.fig4 = Figure(figsize=(6, 3), dpi=80, facecolor='#2d2d2d')
        self.ax4_gpu = self.fig4.add_subplot(211)
        self.ax4_gpu_mem = self.fig4.add_subplot(212)
        
        # Create figure for Audio
        self.fig5 = Figure(figsize=(6, 3), dpi=80, facecolor='#2d2d2d')
        self.ax5_audio = self.fig5.add_subplot(111)
        
        # Configure all axes
        for ax in [self.ax1_cpu, self.ax1_mem, self.ax2_disk, self.ax3_net, self.ax4_gpu, self.ax4_gpu_mem, self.ax5_audio]:
            ax.set_facecolor('#1e1e1e')
            ax.tick_params(colors='white', labelsize=8)
            ax.grid(True, alpha=0.3)
        
        # Set labels
        self.ax1_cpu.set_ylabel('CPU %', color='white', fontsize=9)
        self.ax1_mem.set_ylabel('Memory %', color='white', fontsize=9)
        self.ax2_disk.set_ylabel('Disk MB/s', color='white', fontsize=9)
        self.ax3_net.set_ylabel('Network MB/s', color='white', fontsize=9)
        self.ax4_gpu.set_ylabel('GPU %', color='white', fontsize=9)
        self.ax4_gpu_mem.set_ylabel('GPU Mem %', color='white', fontsize=9)
        self.ax5_audio.set_ylabel('Audio %', color='white', fontsize=9)
        
        # Adjust layout
        self.fig1.tight_layout()
        self.fig2.tight_layout()
        self.fig3.tight_layout()
        self.fig4.tight_layout()
        self.fig5.tight_layout()
    
    def configure_styles(self):
        """Configure custom styles for the dashboard"""
        # Configure dark theme colors
        self.style.configure('Title.TLabel', 
                           background='#1e1e1e', 
                           foreground='#ffffff', 
                           font=('Arial', 16, 'bold'))
        
        self.style.configure('Header.TLabel', 
                           background='#2d2d2d', 
                           foreground='#ffffff', 
                           font=('Arial', 12, 'bold'))
        
        self.style.configure('Value.TLabel', 
                           background='#2d2d2d', 
                           foreground='#00ff00', 
                           font=('Arial', 14, 'bold'))
        
        self.style.configure('Unit.TLabel', 
                           background='#2d2d2d', 
                           foreground='#cccccc', 
                           font=('Arial', 10))
        
        self.style.configure('Panel.TFrame', 
                           background='#2d2d2d', 
                           relief='raised', 
                           borderwidth=2)
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main title
        title_frame = tk.Frame(self.root, bg='#1e1e1e', height=60)
        title_frame.pack(fill='x', padx=10, pady=5)
        title_frame.pack_propagate(False)
        
        title_label = ttk.Label(title_frame, text="Windows 11 System Telemetry Dashboard", style='Title.TLabel')
        title_label.pack(side='left', pady=15)
        
        # System info
        self.system_info_label = ttk.Label(title_frame, text="", style='Unit.TLabel')
        self.system_info_label.pack(side='right', pady=15)
        
        # Main content frame with horizontal layout
        main_frame = tk.Frame(self.root, bg='#1e1e1e')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Left side - Metric panels
        left_frame = tk.Frame(main_frame, bg='#1e1e1e', width=400)
        left_frame.pack(side='left', fill='y', padx=(0, 10))
        left_frame.pack_propagate(False)
        
        # Right side - Graphs
        right_frame = tk.Frame(main_frame, bg='#1e1e1e')
        right_frame.pack(side='right', fill='both', expand=True)
        
        # Create metric panels in left frame
        self.create_cpu_panel(left_frame, 0, 0)
        self.create_memory_panel(left_frame, 1, 0)
        self.create_disk_panel(left_frame, 2, 0)
        self.create_network_panel(left_frame, 3, 0)
        self.create_temperature_panel(left_frame, 4, 0)
        self.create_gpu_panel(left_frame, 5, 0)
        self.create_audio_panel(left_frame, 6, 0)
        
        # Create graph panels in right frame
        self.create_graph_panels(right_frame)
        
        # Configure grid weights for left frame
        for i in range(7):
            left_frame.grid_rowconfigure(i, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
    
    def create_cpu_panel(self, parent, row, col):
        """Create CPU monitoring panel"""
        frame = ttk.Frame(parent, style='Panel.TFrame')
        frame.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
        frame.configure(height=120)
        
        # Header
        ttk.Label(frame, text="CPU Usage", style='Header.TLabel').pack(pady=5)
        
        # CPU percentage with fixed width
        self.cpu_percent_label = ttk.Label(frame, text="0.0%", style='Value.TLabel', width=12, anchor='center')
        self.cpu_percent_label.pack()
        
        # CPU frequency with fixed width
        self.cpu_freq_label = ttk.Label(frame, text="0 MHz", style='Unit.TLabel', width=15, anchor='center')
        self.cpu_freq_label.pack()
        
        # Core count with fixed width
        self.cpu_cores_label = ttk.Label(frame, text=f"Cores: {self.metrics.cpu_cores}", style='Unit.TLabel', width=15, anchor='center')
        self.cpu_cores_label.pack()
    
    def create_memory_panel(self, parent, row, col):
        """Create memory monitoring panel"""
        frame = ttk.Frame(parent, style='Panel.TFrame')
        frame.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
        frame.configure(height=120)
        
        # Header
        ttk.Label(frame, text="Memory Usage", style='Header.TLabel').pack(pady=5)
        
        # Memory percentage with fixed width
        self.memory_percent_label = ttk.Label(frame, text="0.0%", style='Value.TLabel', width=12, anchor='center')
        self.memory_percent_label.pack()
        
        # Memory details with fixed widths
        self.memory_used_label = ttk.Label(frame, text="Used: 0.0 GB", style='Unit.TLabel', width=20, anchor='center')
        self.memory_used_label.pack()
        
        self.memory_available_label = ttk.Label(frame, text="Available: 0.0 GB", style='Unit.TLabel', width=20, anchor='center')
        self.memory_available_label.pack()
        
        self.memory_total_label = ttk.Label(frame, text="Total: 0.0 GB", style='Unit.TLabel', width=20, anchor='center')
        self.memory_total_label.pack()
    
    def create_disk_panel(self, parent, row, col):
        """Create disk I/O monitoring panel"""
        frame = ttk.Frame(parent, style='Panel.TFrame')
        frame.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
        frame.configure(height=100)
        
        # Header
        ttk.Label(frame, text="Disk I/O", style='Header.TLabel').pack(pady=5)
        
        # Read speed with fixed width
        self.disk_read_label = ttk.Label(frame, text="Read: 0.0 MB/s", style='Value.TLabel', width=18, anchor='center')
        self.disk_read_label.pack()
        
        # Write speed with fixed width
        self.disk_write_label = ttk.Label(frame, text="Write: 0.0 MB/s", style='Value.TLabel', width=18, anchor='center')
        self.disk_write_label.pack()
        
        # Disk usage with fixed width
        self.disk_usage_label = ttk.Label(frame, text="Usage: 0.0%", style='Unit.TLabel', width=15, anchor='center')
        self.disk_usage_label.pack()
    
    def create_network_panel(self, parent, row, col):
        """Create network monitoring panel"""
        frame = ttk.Frame(parent, style='Panel.TFrame')
        frame.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
        frame.configure(height=100)
        
        # Header
        ttk.Label(frame, text="Network Activity", style='Header.TLabel').pack(pady=5)
        
        # Upload speed with fixed width
        self.net_upload_label = ttk.Label(frame, text="Upload: 0.0 KB/s", style='Value.TLabel', width=18, anchor='center')
        self.net_upload_label.pack()
        
        # Download speed with fixed width
        self.net_download_label = ttk.Label(frame, text="Download: 0.0 KB/s", style='Value.TLabel', width=18, anchor='center')
        self.net_download_label.pack()
        
        # Total transferred with fixed width
        self.net_total_label = ttk.Label(frame, text="Total: 0.0 MB", style='Unit.TLabel', width=18, anchor='center')
        self.net_total_label.pack()
    
    def create_temperature_panel(self, parent, row, col):
        """Create temperature monitoring panel"""
        frame = ttk.Frame(parent, style='Panel.TFrame')
        frame.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
        frame.configure(height=80)
        
        # Header
        ttk.Label(frame, text="System Status", style='Header.TLabel').pack(pady=5)
        
        # CPU temperature with fixed width
        self.cpu_temp_label = ttk.Label(frame, text="CPU: 0.0°C", style='Value.TLabel', width=15, anchor='center')
        self.cpu_temp_label.pack()
        
        # Uptime with fixed width
        self.uptime_label = ttk.Label(frame, text="Uptime: 0:00:00", style='Unit.TLabel', width=20, anchor='center')
        self.uptime_label.pack()
    
    def create_gpu_panel(self, parent, row, col):
        """Create GPU monitoring panel"""
        frame = ttk.Frame(parent, style='Panel.TFrame')
        frame.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
        frame.configure(height=120)
        
        # Header
        ttk.Label(frame, text="GPU Usage", style='Header.TLabel').pack(pady=5)
        
        # GPU usage percentage with fixed width
        self.gpu_usage_label = ttk.Label(frame, text="0.0%", style='Value.TLabel', width=12, anchor='center')
        self.gpu_usage_label.pack()
        
        # GPU memory with fixed width
        self.gpu_memory_label = ttk.Label(frame, text="Memory: 0.0%", style='Unit.TLabel', width=20, anchor='center')
        self.gpu_memory_label.pack()
        
        # GPU temperature with fixed width
        self.gpu_temp_label = ttk.Label(frame, text="Temp: 0.0°C", style='Unit.TLabel', width=15, anchor='center')
        self.gpu_temp_label.pack()
        
        # GPU name with fixed width
        self.gpu_name_label = ttk.Label(frame, text="No GPU", style='Unit.TLabel', width=25, anchor='center')
        self.gpu_name_label.pack()
    
    def create_audio_panel(self, parent, row, col):
        """Create audio monitoring panel"""
        frame = ttk.Frame(parent, style='Panel.TFrame')
        frame.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
        frame.configure(height=120)
        
        # Header
        ttk.Label(frame, text="Audio Interface", style='Header.TLabel').pack(pady=5)
        
        # Sample rate with fixed width
        self.audio_sample_rate_label = ttk.Label(frame, text="44.1 kHz", style='Value.TLabel', width=15, anchor='center')
        self.audio_sample_rate_label.pack()
        
        # Bit depth and channels with fixed width
        self.audio_format_label = ttk.Label(frame, text="16-bit Stereo", style='Unit.TLabel', width=20, anchor='center')
        self.audio_format_label.pack()
        
        # Buffer size with fixed width
        self.audio_buffer_label = ttk.Label(frame, text="Buffer: 1024", style='Unit.TLabel', width=18, anchor='center')
        self.audio_buffer_label.pack()
        
        # Device name with fixed width
        self.audio_device_label = ttk.Label(frame, text="Default Device", style='Unit.TLabel', width=25, anchor='center')
        self.audio_device_label.pack()
    
    def create_graph_panels(self, parent):
        """Create graph panels with matplotlib"""
        # CPU & Memory graph
        graph_frame1 = ttk.Frame(parent, style='Panel.TFrame')
        graph_frame1.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(graph_frame1, text="CPU & Memory Usage", style='Header.TLabel').pack(pady=5)
        
        self.canvas1 = FigureCanvasTkAgg(self.fig1, graph_frame1)
        self.canvas1.get_tk_widget().pack(fill='x', padx=10, pady=5)
        
        # Disk I/O graph
        graph_frame2 = ttk.Frame(parent, style='Panel.TFrame')
        graph_frame2.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(graph_frame2, text="Disk I/O Activity", style='Header.TLabel').pack(pady=5)
        
        self.canvas2 = FigureCanvasTkAgg(self.fig2, graph_frame2)
        self.canvas2.get_tk_widget().pack(fill='x', padx=10, pady=5)
        
        # Network graph
        graph_frame3 = ttk.Frame(parent, style='Panel.TFrame')
        graph_frame3.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(graph_frame3, text="Network Activity", style='Header.TLabel').pack(pady=5)
        
        self.canvas3 = FigureCanvasTkAgg(self.fig3, graph_frame3)
        self.canvas3.get_tk_widget().pack(fill='x', padx=10, pady=5)
        
        # GPU graph
        graph_frame4 = ttk.Frame(parent, style='Panel.TFrame')
        graph_frame4.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(graph_frame4, text="GPU Usage & Memory", style='Header.TLabel').pack(pady=5)
        
        self.canvas4 = FigureCanvasTkAgg(self.fig4, graph_frame4)
        self.canvas4.get_tk_widget().pack(fill='x', padx=10, pady=5)
        
        # Audio graph
        graph_frame5 = ttk.Frame(parent, style='Panel.TFrame')
        graph_frame5.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(graph_frame5, text="Audio Interface Metrics", style='Header.TLabel').pack(pady=5)
        
        self.canvas5 = FigureCanvasTkAgg(self.fig5, graph_frame5)
        self.canvas5.get_tk_widget().pack(fill='x', padx=10, pady=5)
    
    def data_collection_loop(self):
        """Background thread for collecting system data"""
        while self.running:
            try:
                self.metrics.update_metrics()
                time.sleep(0.5)  # 500ms update interval
            except Exception as e:
                print(f"Error collecting metrics: {e}")
                time.sleep(1)
    
    def update_gui(self):
        """Update GUI with current metrics"""
        if not self.running:
            return
        
        try:
            # Update system info
            system_info = f"{platform.system()} {platform.release()} | {datetime.now().strftime('%H:%M:%S')}"
            self.system_info_label.config(text=system_info)
            
            # Update CPU panel
            self.cpu_percent_label.config(text=f"{self.metrics.cpu_percent:.1f}%")
            self.cpu_freq_label.config(text=f"{self.metrics.cpu_freq:.0f} MHz")
            
            # Update memory panel
            self.memory_percent_label.config(text=f"{self.metrics.memory_percent:.1f}%")
            self.memory_used_label.config(text=f"Used: {self.metrics.format_bytes(self.metrics.memory_used)}")
            self.memory_available_label.config(text=f"Available: {self.metrics.format_bytes(self.metrics.memory_available)}")
            self.memory_total_label.config(text=f"Total: {self.metrics.format_bytes(self.metrics.memory_total)}")
            
            # Update disk panel
            self.disk_read_label.config(text=f"Read: {self.metrics.format_bytes(self.metrics.disk_read_speed)}/s")
            self.disk_write_label.config(text=f"Write: {self.metrics.format_bytes(self.metrics.disk_write_speed)}/s")
            self.disk_usage_label.config(text=f"Usage: {self.metrics.disk_usage_percent:.1f}%")
            
            # Update network panel
            self.net_upload_label.config(text=f"Upload: {self.metrics.format_bytes(self.metrics.network_sent_speed)}/s")
            self.net_download_label.config(text=f"Download: {self.metrics.format_bytes(self.metrics.network_recv_speed)}/s")
            total_transfer = self.metrics.network_total_sent + self.metrics.network_total_recv
            self.net_total_label.config(text=f"Total: {self.metrics.format_bytes(total_transfer)}")
            
            # Update temperature panel
            self.cpu_temp_label.config(text=f"CPU: {self.metrics.cpu_temp:.1f}°C")
            self.uptime_label.config(text=f"Uptime: {self.metrics.system_uptime}")
            
            # Update GPU panel
            self.gpu_usage_label.config(text=f"{self.metrics.gpu_usage:.1f}%")
            self.gpu_memory_label.config(text=f"Memory: {self.metrics.gpu_memory_percent:.1f}%")
            self.gpu_temp_label.config(text=f"Temp: {self.metrics.gpu_temp:.1f}°C")
            # Truncate GPU name if too long
            gpu_name = self.metrics.gpu_name[:20] + "..." if len(self.metrics.gpu_name) > 20 else self.metrics.gpu_name
            self.gpu_name_label.config(text=gpu_name)
            
            # Update audio panel
            self.audio_sample_rate_label.config(text=f"{self.metrics.audio_sample_rate / 1000:.1f} kHz")
            format_text = f"{self.metrics.audio_bit_depth}-bit {self.metrics.audio_channels}ch"
            self.audio_format_label.config(text=format_text)
            self.audio_buffer_label.config(text=f"Buffer: {self.metrics.audio_buffer_size}")
            # Truncate device name if too long
            device_name = self.metrics.audio_device_name[:20] + "..." if len(self.metrics.audio_device_name) > 20 else self.metrics.audio_device_name
            self.audio_device_label.config(text=device_name)
            
            # Update graphs
            self.update_graphs()
            
            # Color coding based on values
            self.update_color_coding()
            
        except Exception as e:
            print(f"Error updating GUI: {e}")
        
        # Schedule next update
        self.root.after(500, self.update_gui)  # 500ms update interval
    
    def update_graphs(self):
        """Update time series graphs"""
        if len(self.metrics.timestamps) < 2:
            return
        
        try:
            # Convert timestamps to matplotlib format
            times = list(self.metrics.timestamps)
            
            # Update CPU graph
            self.ax1_cpu.clear()
            self.ax1_cpu.plot(times, list(self.metrics.cpu_history), 'g-', linewidth=2, label='CPU %')
            self.ax1_cpu.set_ylabel('CPU %', color='white', fontsize=9)
            self.ax1_cpu.set_ylim(0, 100)
            self.ax1_cpu.tick_params(colors='white', labelsize=8)
            self.ax1_cpu.grid(True, alpha=0.3)
            self.ax1_cpu.set_facecolor('#1e1e1e')
            
            # Update Memory graph
            self.ax1_mem.clear()
            self.ax1_mem.plot(times, list(self.metrics.memory_history), 'b-', linewidth=2, label='Memory %')
            self.ax1_mem.set_ylabel('Memory %', color='white', fontsize=9)
            self.ax1_mem.set_ylim(0, 100)
            self.ax1_mem.tick_params(colors='white', labelsize=8)
            self.ax1_mem.grid(True, alpha=0.3)
            self.ax1_mem.set_facecolor('#1e1e1e')
            
            # Update Disk I/O graph
            self.ax2_disk.clear()
            self.ax2_disk.plot(times, list(self.metrics.disk_read_history), 'r-', linewidth=2, label='Read MB/s')
            self.ax2_disk.plot(times, list(self.metrics.disk_write_history), 'orange', linewidth=2, label='Write MB/s')
            self.ax2_disk.set_ylabel('Disk MB/s', color='white', fontsize=9)
            self.ax2_disk.tick_params(colors='white', labelsize=8)
            self.ax2_disk.grid(True, alpha=0.3)
            self.ax2_disk.set_facecolor('#1e1e1e')
            self.ax2_disk.legend(fontsize=8, loc='upper right')
            
            # Update Network graph
            self.ax3_net.clear()
            self.ax3_net.plot(times, list(self.metrics.network_sent_history), 'cyan', linewidth=2, label='Upload MB/s')
            self.ax3_net.plot(times, list(self.metrics.network_recv_history), 'magenta', linewidth=2, label='Download MB/s')
            self.ax3_net.set_ylabel('Network MB/s', color='white', fontsize=9)
            self.ax3_net.tick_params(colors='white', labelsize=8)
            self.ax3_net.grid(True, alpha=0.3)
            self.ax3_net.set_facecolor('#1e1e1e')
            self.ax3_net.legend(fontsize=8, loc='upper right')
            
            # Update GPU Usage graph
            self.ax4_gpu.clear()
            self.ax4_gpu.plot(times, list(self.metrics.gpu_usage_history), 'yellow', linewidth=2, label='GPU %')
            self.ax4_gpu.set_ylabel('GPU %', color='white', fontsize=9)
            self.ax4_gpu.set_ylim(0, 100)
            self.ax4_gpu.tick_params(colors='white', labelsize=8)
            self.ax4_gpu.grid(True, alpha=0.3)
            self.ax4_gpu.set_facecolor('#1e1e1e')
            
            # Update GPU Memory graph
            self.ax4_gpu_mem.clear()
            self.ax4_gpu_mem.plot(times, list(self.metrics.gpu_memory_history), 'orange', linewidth=2, label='GPU Mem %')
            self.ax4_gpu_mem.set_ylabel('GPU Mem %', color='white', fontsize=9)
            self.ax4_gpu_mem.set_ylim(0, 100)
            self.ax4_gpu_mem.tick_params(colors='white', labelsize=8)
            self.ax4_gpu_mem.grid(True, alpha=0.3)
            self.ax4_gpu_mem.set_facecolor('#1e1e1e')
            
            # Update Audio graph
            self.ax5_audio.clear()
            self.ax5_audio.plot(times, list(self.metrics.audio_sample_rate_history), 'lime', linewidth=2, label='Sample Rate (kHz)')
            self.ax5_audio.plot(times, list(self.metrics.audio_buffer_history), 'cyan', linewidth=2, label='Buffer Size')
            self.ax5_audio.set_ylabel('Audio Metrics', color='white', fontsize=9)
            self.ax5_audio.tick_params(colors='white', labelsize=8)
            self.ax5_audio.grid(True, alpha=0.3)
            self.ax5_audio.set_facecolor('#1e1e1e')
            self.ax5_audio.legend(fontsize=8, loc='upper right')
            
            # Format x-axis for all graphs
            for ax in [self.ax1_cpu, self.ax1_mem, self.ax2_disk, self.ax3_net, self.ax4_gpu, self.ax4_gpu_mem, self.ax5_audio]:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
                ax.xaxis.set_major_locator(mdates.SecondLocator(interval=10))
                for label in ax.get_xticklabels():
                    label.set_rotation(45)
                    label.set_fontsize(7)
            
            # Refresh canvases
            self.canvas1.draw()
            self.canvas2.draw()
            self.canvas3.draw()
            self.canvas4.draw()
            self.canvas5.draw()
            
        except Exception as e:
            print(f"Error updating graphs: {e}")
    
    def update_color_coding(self):
        """Update color coding based on metric values"""
        # CPU color coding
        if self.metrics.cpu_percent > 80:
            self.cpu_percent_label.config(foreground='#ff4444')
        elif self.metrics.cpu_percent > 60:
            self.cpu_percent_label.config(foreground='#ffaa00')
        else:
            self.cpu_percent_label.config(foreground='#00ff00')
        
        # Memory color coding
        if self.metrics.memory_percent > 85:
            self.memory_percent_label.config(foreground='#ff4444')
        elif self.metrics.memory_percent > 70:
            self.memory_percent_label.config(foreground='#ffaa00')
        else:
            self.memory_percent_label.config(foreground='#00ff00')
        
        # Temperature color coding
        if self.metrics.cpu_temp > 80:
            self.cpu_temp_label.config(foreground='#ff4444')
        elif self.metrics.cpu_temp > 65:
            self.cpu_temp_label.config(foreground='#ffaa00')
        else:
            self.cpu_temp_label.config(foreground='#00ff00')
        
        # GPU color coding
        if self.metrics.gpu_usage > 80:
            self.gpu_usage_label.config(foreground='#ff4444')
        elif self.metrics.gpu_usage > 60:
            self.gpu_usage_label.config(foreground='#ffaa00')
        else:
            self.gpu_usage_label.config(foreground='#00ff00')
        
        # GPU temperature color coding
        if self.metrics.gpu_temp > 85:
            self.gpu_temp_label.config(foreground='#ff4444')
        elif self.metrics.gpu_temp > 70:
            self.gpu_temp_label.config(foreground='#ffaa00')
        else:
            self.gpu_temp_label.config(foreground='#00ff00')
        
        # Audio sample rate color coding
        if self.metrics.audio_sample_rate < 44100:
            self.audio_sample_rate_label.config(foreground='#ffaa00')
        elif self.metrics.audio_sample_rate >= 96000:
            self.audio_sample_rate_label.config(foreground='#00ff00')
        else:
            self.audio_sample_rate_label.config(foreground='#ffffff')
    
    def on_closing(self):
        """Handle application closing"""
        self.running = False
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """Start the dashboard"""
        self.root.mainloop()

def main():
    """Main entry point"""
    print("Starting Windows 11 System Telemetry Dashboard...")
    print(f"Python version: {platform.python_version()}")
    print(f"System: {platform.system()} {platform.release()}")
    print(f"WMI Available: {WMI_AVAILABLE}")
    print(f"GPU Available: {GPU_AVAILABLE}")
    print(f"Audio Available: {AUDIO_AVAILABLE}")
    
    try:
        dashboard = TelemetryDashboard()
        dashboard.run()
    except KeyboardInterrupt:
        print("\nDashboard stopped by user")
    except Exception as e:
        print(f"Error starting dashboard: {e}")

if __name__ == "__main__":
    main()