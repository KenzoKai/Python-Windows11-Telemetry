# Arduino Giga R1 WiFi Telemetry Display System

This project creates a real-time system telemetry display using an Arduino Giga R1 WiFi with Giga Display Shield. The system consists of a Python client that collects system metrics and sends them via WiFi to the Arduino, which displays the data on a beautiful landscape-oriented dashboard interface.

## Multi-GPU Support

The system now supports multiple GPUs and intelligently prioritizes discrete NVIDIA GPUs (like RTX 3090) over integrated graphics (like AMD Radeon integrated). It will automatically detect and use the most powerful GPU available for monitoring.

## Hardware Requirements

- **Arduino Giga R1 WiFi** - Main microcontroller with WiFi capability
- **Arduino Giga Display Shield** - 800x480 TFT display with touch capability
- **WiFi Network** - Both the PC and Arduino must be on the same network

## Software Requirements

### Python Client Dependencies
- Python 3.7 or higher
- psutil (system monitoring)
- ArduinoJson (for JSON parsing)
- Optional: wmi, GPUtil, nvidia-ml-py3 (for enhanced monitoring)

### Arduino Libraries
- WiFi (built-in)
- ArduinoJson (install via Library Manager)
- Arduino_GigaDisplay_GFX (install via Library Manager)
- Arduino_GigaDisplay (install via Library Manager)

## Installation

### 1. Python Client Setup

1. Install required Python packages:
```bash
pip install psutil
pip install wmi  # Windows only, for temperature monitoring
pip install GPUtil  # For GPU monitoring
pip install nvidia-ml-py3  # For NVIDIA GPU monitoring
```

2. Run the client:
```bash
python arduino_telemetry_client.py
```

### 2. Arduino Setup

1. Install required libraries in Arduino IDE:
   - Open Arduino IDE
   - Go to Tools → Manage Libraries
   - Search and install:
     - "ArduinoJson" by Benoit Blanchon
     - "Arduino_GigaDisplay_GFX"
     - "Arduino_GigaDisplay"

2. Configure WiFi credentials:
   - Open `arduino_telemetry_display.ino`
   - Update these lines with your WiFi credentials:
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```

3. Upload the code to your Arduino Giga R1

## System Architecture

### Data Flow
1. **Python Client** (`arduino_telemetry_client.py`)
   - Collects system metrics every 2 seconds
   - Formats data as JSON
   - Sends via TCP socket to Arduino

2. **Arduino Display** (`arduino_telemetry_display.ino`)
   - Acts as WiFi server on port 8080
   - Receives JSON telemetry data
   - Parses and displays on 800x480 TFT screen

### Telemetry Data Collected

#### CPU Metrics
- Usage percentage
- Frequency (MHz)
- Core count
- Temperature (°C)

#### Memory Metrics
- Usage percentage
- Used memory (GB)
- Total memory (GB)

#### Disk I/O Metrics
- Read speed (MB/s)
- Write speed (MB/s)
- Disk usage percentage

#### Network Metrics
- Upload speed (MB/s)
- Download speed (MB/s)

#### GPU Metrics
- Usage percentage
- Memory usage percentage
- Temperature (°C)
- GPU name

#### System Metrics
- Platform (Windows/Linux/macOS)
- System uptime
- Connection status

## Display Layout

The Arduino display shows an 8-panel dashboard:

```
┌─────────────────────────────────────────────────────────────┐
│                System Telemetry Dashboard        CONNECTED  │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│    CPU      │   MEMORY    │  DISK I/O   │    NETWORK      │
│   45.2%     │   67.8%     │ R: 12.3MB/s │ UP: 0.5 MB/s    │
│ 3200 MHz    │Used: 8.1GB  │ W: 5.7MB/s  │ DN: 2.1 MB/s    │
│ Cores: 8    │Total: 16GB  │Usage: 78.2% │Activity: 2.6MB/s│
│ ████████░░  │ ██████████░ │ ████████░░  │                 │
├─────────────┼─────────────┼─────────────┼─────────────────┤
│    GPU      │   SYSTEM    │    TEMPS    │     STATUS      │
│   23.4%     │  Windows    │ CPU: 52.1°C │    ONLINE       │
│ Mem: 15.2%  │Uptime: 5h2m │ GPU: 45.8°C │   WiFi: OK      │
│RTX 3090     │Updated: 1s  │    COOL     │IP: 192.168.1.100│
│ ██░░░░░░░░  │             │             │                 │
└─────────────┴─────────────┴─────────────┴─────────────────┘
```

## Features

### Visual Indicators
- **Color-coded values**: Green (good), Yellow (warning), Red (critical)
- **Progress bars**: Visual representation of usage percentages
- **Real-time updates**: Data refreshes every 2 seconds
- **Connection status**: Shows online/offline status

### Temperature Monitoring
- CPU temperature with color coding
- GPU temperature monitoring
- Overall thermal status indicator

### Network Connectivity
- Automatic WiFi connection
- Connection status monitoring
- IP address display
- Data timeout detection

## Configuration

### Python Client Configuration
Edit `arduino_telemetry_client.py` to modify:
- Arduino IP address (default: 192.168.1.100)
- Update interval (default: 2 seconds)
- Port number (default: 8080)

### Arduino Configuration
Edit `arduino_telemetry_display.ino` to modify:
- WiFi credentials
- Display colors and layout
- Panel arrangement
- Update intervals

## Troubleshooting

### Common Issues

1. **WiFi Connection Failed**
   - Check WiFi credentials in Arduino code
   - Ensure Arduino is within WiFi range
   - Verify network allows device connections

2. **Python Client Can't Connect**
   - Check Arduino IP address
   - Ensure both devices are on same network
   - Verify port 8080 is not blocked by firewall

3. **No Data Display**
   - Check serial monitor for error messages
   - Verify JSON parsing is working
   - Ensure Python client is sending data

4. **Display Issues**
   - Check display shield connections
   - Verify display libraries are installed
   - Try different display initialization

### Debug Information

#### Arduino Serial Output
```
Arduino Giga R1 Telemetry Display
==================================
WiFi connected!
IP address: 192.168.1.100
Server started on port 8080
New client connected
Telemetry data updated
```

#### Python Client Output
```
Arduino Telemetry Client
========================
Enter Arduino IP address (default: 192.168.1.100): 
Connected to Arduino at 192.168.1.100:8080
Sent: CPU 45.2%, Memory 67.8%, GPU 23.4%
```

## Performance

- **Update Rate**: 2 seconds (configurable)
- **Data Latency**: < 100ms over WiFi
- **Display Refresh**: 10 FPS
- **Memory Usage**: ~512KB JSON buffer
- **Power Consumption**: ~500mA @ 5V

## Customization

### Adding New Metrics
1. Modify Python client to collect additional data
2. Update JSON structure
3. Add parsing in Arduino code
4. Create new display panel

### Changing Display Layout
1. Modify panel positions in Arduino code
2. Adjust `PANEL_WIDTH`, `PANEL_HEIGHT` constants
3. Update drawing functions
4. Recompile and upload

### Color Themes
Modify color constants in Arduino code:
```cpp
#define CUSTOM_COLOR 0x07E0  // RGB565 format
```

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review serial monitor output
3. Verify hardware connections
4. Check library versions

## Future Enhancements

- Touch interface for settings
- Data logging to SD card
- Multiple system monitoring
- Web interface for configuration
- Historical data graphs
- Alert notifications