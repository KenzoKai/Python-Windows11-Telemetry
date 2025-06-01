# Windows 11 System Telemetry Dashboard

A real-time system monitoring dashboard built with Python and Tkinter, specifically designed for Windows 11. The dashboard displays live system telemetry including CPU usage, memory consumption, disk I/O, network activity, GPU monitoring, audio interface metrics, and system temperatures.

## Features

- **Real-time Monitoring**: Updates every 500ms for responsive system monitoring
- **Comprehensive Metrics**:
  - CPU usage percentage and frequency
  - Memory usage with detailed breakdown
  - Disk I/O read/write speeds and usage
  - Network upload/download speeds and total transfer
  - GPU usage, memory, and temperature (NVIDIA and general GPU support)
  - Audio interface metrics (sample rate, bit depth, buffer size)
  - System temperatures (CPU/GPU) and uptime
- **Color-coded Indicators**: Visual alerts for high resource usage
- **Dark Theme**: Professional dark interface optimized for extended use
- **Low Resource Usage**: Efficient background data collection
- **Windows 11 Optimized**: Leverages Windows-specific APIs for accurate data

## Requirements

- Windows 11 (or Windows 10)
- Python 3.7 or higher
- Administrator privileges (recommended for temperature monitoring)

## Installation

1. **Clone or download the project files**
   ```bash
   # If using git
   git clone <repository-url>
   cd windows-telemetry-dashboard
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   Or install manually:
   ```bash
   pip install psutil WMI matplotlib GPUtil pycaw comtypes nvidia-ml-py3
   ```

3. **Run the dashboard**
   ```bash
   python dashboard.py
   ```

## Usage

### Starting the Dashboard
```bash
python dashboard.py
```

The dashboard will open in a new window and immediately start collecting and displaying system metrics.

### Dashboard Layout

The dashboard is organized into seven main sections:

1. **CPU Panel**
   - Current CPU usage percentage
   - CPU frequency in MHz
   - Number of CPU cores

2. **Memory Panel**
   - Memory usage percentage
   - Used, available, and total memory in human-readable format

3. **Disk I/O Panel**
   - Real-time read/write speeds
   - Overall disk usage percentage

4. **Network Panel**
   - Upload and download speeds
   - Total data transferred since startup

5. **Temperature & Status Panel**
   - CPU temperature (when available)
   - System uptime

6. **GPU Panel**
   - GPU usage percentage
   - GPU memory usage and percentage
   - GPU temperature
   - GPU name/model

7. **Audio Interface Panel**
   - Audio sample rate (kHz)
   - Bit depth and channel configuration
   - Buffer size
   - Audio device name

### Color Coding

The dashboard uses color coding to indicate system health:

- **Green**: Normal operation
- **Orange**: Moderate usage (warning)
- **Red**: High usage (critical)

**CPU Usage:**
- Green: < 60%
- Orange: 60-80%
- Red: > 80%

**Memory Usage:**
- Green: < 70%
- Orange: 70-85%
- Red: > 85%

**Temperature:**
- Green: < 65°C
- Orange: 65-80°C
- Red: > 80°C

## Technical Details

### Architecture

- **Data Collection**: Background thread using `psutil` and `WMI` libraries
- **GUI Framework**: Tkinter with custom dark theme styling
- **Update Frequency**: 500ms refresh rate for real-time monitoring
- **Threading**: Non-blocking data collection to maintain responsive UI

### Dependencies

- **psutil**: Cross-platform system and process utilities
- **WMI**: Windows Management Instrumentation for temperature data
- **matplotlib**: Plotting library for real-time graphs
- **GPUtil**: GPU monitoring and statistics
- **nvidia-ml-py3**: NVIDIA GPU monitoring via NVML
- **pycaw**: Windows Core Audio API for audio device information
- **comtypes**: COM interface support for Windows APIs

### Hardware Monitoring

**Temperature Monitoring:**
Temperature monitoring requires WMI access and may need administrator privileges. If WMI is not available or accessible, the dashboard will:
- Display a fallback estimated temperature based on CPU usage
- Continue to function normally for all other metrics
- Show a warning message in the console

**GPU Monitoring:**
GPU monitoring supports multiple detection methods:
- NVIDIA GPUs via NVML (nvidia-ml-py3) for detailed metrics
- General GPU detection via GPUtil for broader compatibility
- Graceful fallback when no GPU libraries are available

**Audio Interface Monitoring:**
Audio monitoring provides interface specifications:
- Sample rate, bit depth, and channel configuration
- Buffer size information
- Default audio device detection
- Graceful handling when audio APIs are unavailable

## Troubleshooting

### Common Issues

1. **"WMI not available" message**
   - Install WMI: `pip install WMI`
   - Run as administrator for better hardware access

2. **Temperature shows 0°C or unrealistic values**
   - Run the application as administrator
   - Some systems may not expose temperature sensors via WMI

3. **High CPU usage from the dashboard itself**
   - This is normal during the first few seconds as metrics stabilize
   - If persistent, check for other system issues

4. **Network speeds show as 0**
   - Wait a few seconds for initial measurements to stabilize
   - Ensure network activity is present for accurate readings

### Performance Notes

- The dashboard uses minimal system resources (typically < 1% CPU)
- Memory usage is optimized with efficient data structures
- Background data collection runs in a separate thread

## Customization

### Modifying Update Frequency

To change the update frequency, modify these values in `dashboard.py`:

```python
# In data_collection_loop method
time.sleep(0.5)  # Change to desired interval in seconds

# In update_gui method
self.root.after(500, self.update_gui)  # Change to desired interval in milliseconds
```

### Adding New Metrics

The dashboard is designed to be extensible. To add new metrics:

1. Add data collection in the `SystemMetrics.update_metrics()` method
2. Create a new panel in the `TelemetryDashboard.create_widgets()` method
3. Update the GUI in the `TelemetryDashboard.update_gui()` method

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## System Compatibility

- **Primary Target**: Windows 11
- **Secondary Support**: Windows 10
- **Python Versions**: 3.7, 3.8, 3.9, 3.10, 3.11, 3.12
- **Architecture**: x64, x86 (ARM support depends on Python installation)