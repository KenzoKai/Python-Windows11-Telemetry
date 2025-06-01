/*
  Arduino Giga R1 WiFi Telemetry Display
  Receives system telemetry data via WiFi and displays on Giga Display Shield
  
  Hardware:
  - Arduino Giga R1 WiFi
  - Arduino Giga Display Shield
  
  Libraries required:
  - WiFi
  - ArduinoJson
  - Arduino_GigaDisplay_GFX
  - Arduino_GigaDisplay
*/

#include <WiFi.h>
#include <ArduinoJson.h>
#include "Arduino_GigaDisplay_GFX.h"

// WiFi credentials
const char* ssid = "Yojimbo";
const char* password = "discord1";

// Server settings
const int serverPort = 8080;
WiFiServer server(serverPort);
WiFiClient client;

// Display setup
GigaDisplay_GFX display;

// Colors (RGB565 format)
#define BLACK       0x0000
#define WHITE       0xFFFF
#define RED         0xF800
#define GREEN       0x07E0
#define BLUE        0x001F
#define YELLOW      0xFFE0
#define CYAN        0x07FF
#define MAGENTA     0xF81F
#define ORANGE      0xFD20
#define GRAY        0x8410
#define DARK_GRAY   0x4208
#define LIGHT_GRAY  0xC618

// Display dimensions
#define SCREEN_WIDTH  800
#define SCREEN_HEIGHT 480

// Layout constants
#define HEADER_HEIGHT 60
#define PANEL_WIDTH   190
#define PANEL_HEIGHT  140
#define MARGIN        10
#define PANELS_PER_ROW 4

// Telemetry data structure
struct TelemetryData {
  // CPU
  float cpu_usage;
  float cpu_frequency;
  int cpu_cores;
  float cpu_temperature;
  
  // Memory
  float memory_usage_percent;
  float memory_used_gb;
  float memory_total_gb;
  
  // Disk
  float disk_read_speed;
  float disk_write_speed;
  float disk_usage_percent;
  
  // Network
  float network_upload_speed;
  float network_download_speed;
  
  // GPU
  float gpu_usage;
  float gpu_memory_percent;
  float gpu_temperature;
  String gpu_name;
  
  // System
  int uptime_hours;
  int uptime_minutes;
  String platform;
  String timestamp;
  
  // Connection status
  bool data_valid;
  unsigned long last_update;
};

TelemetryData telemetry;

void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);
  
  Serial.println("Arduino Giga R1 Telemetry Display");
  Serial.println("==================================");
  
  // Initialize display
  display.begin();
  display.setRotation(1);  // Set to landscape orientation (0=portrait, 1=landscape, 2=portrait flipped, 3=landscape flipped)
  display.fillScreen(BLACK);
  display.setTextColor(WHITE);
  display.setTextSize(2);
  display.setCursor(10, 10);
  display.println("Initializing...");
  
  // Initialize telemetry data
  telemetry.data_valid = false;
  telemetry.last_update = 0;
  
  // Connect to WiFi
  connectToWiFi();
  
  // Start server
  server.begin();
  Serial.print("Server started on port ");
  Serial.println(serverPort);
  
  // Display initial screen
  drawInitialScreen();
}

void loop() {
  // Check for incoming connections
  WiFiClient newClient = server.available();
  if (newClient) {
    Serial.println("New client connected");
    client = newClient;
  }
  
  // Read telemetry data if client is connected
  if (client && client.connected()) {
    if (client.available()) {
      String jsonString = client.readStringUntil('\n');
      if (jsonString.length() > 0) {
        parseTelemetryData(jsonString);
      }
    }
  }
  
  // Update display
  updateDisplay();
  
  // Check connection status
  checkConnectionStatus();
  
  delay(100);
}

void connectToWiFi() {
  display.fillScreen(BLACK);
  display.setTextColor(WHITE);
  display.setTextSize(2);
  display.setCursor(10, 10);
  display.println("Connecting to WiFi...");
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(1000);
    Serial.print(".");
    display.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("WiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    
    display.fillScreen(BLACK);
    display.setCursor(10, 10);
    display.println("WiFi Connected!");
    display.print("IP: ");
    display.println(WiFi.localIP());
    delay(2000);
  } else {
    Serial.println("WiFi connection failed!");
    display.fillScreen(BLACK);
    display.setCursor(10, 10);
    display.setTextColor(RED);
    display.println("WiFi Failed!");
    while (1) delay(1000);
  }
}

void parseTelemetryData(String jsonString) {
  StaticJsonDocument<1024> doc;
  DeserializationError error = deserializeJson(doc, jsonString);
  
  if (error) {
    Serial.print("JSON parsing failed: ");
    Serial.println(error.c_str());
    return;
  }
  
  // Parse CPU data
  telemetry.cpu_usage = doc["cpu"]["usage"];
  telemetry.cpu_frequency = doc["cpu"]["frequency"];
  telemetry.cpu_cores = doc["cpu"]["cores"];
  telemetry.cpu_temperature = doc["cpu"]["temperature"];
  
  // Parse Memory data
  telemetry.memory_usage_percent = doc["memory"]["usage_percent"];
  telemetry.memory_used_gb = doc["memory"]["used_gb"];
  telemetry.memory_total_gb = doc["memory"]["total_gb"];
  
  // Parse Disk data
  telemetry.disk_read_speed = doc["disk"]["read_speed"];
  telemetry.disk_write_speed = doc["disk"]["write_speed"];
  telemetry.disk_usage_percent = doc["disk"]["usage_percent"];
  
  // Parse Network data
  telemetry.network_upload_speed = doc["network"]["upload_speed"];
  telemetry.network_download_speed = doc["network"]["download_speed"];
  
  // Parse GPU data
  telemetry.gpu_usage = doc["gpu"]["usage"];
  telemetry.gpu_memory_percent = doc["gpu"]["memory_percent"];
  telemetry.gpu_temperature = doc["gpu"]["temperature"];
  telemetry.gpu_name = doc["gpu"]["name"].as<String>();
  
  // Parse System data
  telemetry.uptime_hours = doc["system"]["uptime_hours"];
  telemetry.uptime_minutes = doc["system"]["uptime_minutes"];
  telemetry.platform = doc["system"]["platform"].as<String>();
  telemetry.timestamp = doc["timestamp"].as<String>();
  
  telemetry.data_valid = true;
  telemetry.last_update = millis();
  
  Serial.println("Telemetry data updated");
}

void drawInitialScreen() {
  display.fillScreen(BLACK);
  
  // Draw header
  drawHeader();
  
  // Draw panel outlines
  drawPanelOutlines();
  
  // Draw labels
  drawPanelLabels();
}

void drawHeader() {
  display.fillRect(0, 0, SCREEN_WIDTH, HEADER_HEIGHT, DARK_GRAY);
  display.setTextColor(WHITE);
  display.setTextSize(3);
  display.setCursor(10, 15);
  display.println("System Telemetry Dashboard");
  
  // Connection status
  display.setTextSize(2);
  display.setCursor(SCREEN_WIDTH - 200, 20);
  if (telemetry.data_valid && (millis() - telemetry.last_update < 10000)) {
    display.setTextColor(GREEN);
    display.println("CONNECTED");
  } else {
    display.setTextColor(RED);
    display.println("WAITING...");
  }
}

void drawPanelOutlines() {
  int x, y;
  
  // Draw 8 panels in 2 rows
  for (int row = 0; row < 2; row++) {
    for (int col = 0; col < 4; col++) {
      x = MARGIN + col * (PANEL_WIDTH + MARGIN);
      y = HEADER_HEIGHT + MARGIN + row * (PANEL_HEIGHT + MARGIN);
      
      display.drawRect(x, y, PANEL_WIDTH, PANEL_HEIGHT, LIGHT_GRAY);
    }
  }
}

void drawPanelLabels() {
  display.setTextSize(2);
  display.setTextColor(CYAN);
  
  // Row 1 labels
  display.setCursor(MARGIN + 10, HEADER_HEIGHT + MARGIN + 10);
  display.println("CPU");
  
  display.setCursor(MARGIN + PANEL_WIDTH + MARGIN + 10, HEADER_HEIGHT + MARGIN + 10);
  display.println("MEMORY");
  
  display.setCursor(MARGIN + 2 * (PANEL_WIDTH + MARGIN) + 10, HEADER_HEIGHT + MARGIN + 10);
  display.println("DISK I/O");
  
  display.setCursor(MARGIN + 3 * (PANEL_WIDTH + MARGIN) + 10, HEADER_HEIGHT + MARGIN + 10);
  display.println("NETWORK");
  
  // Row 2 labels
  display.setCursor(MARGIN + 10, HEADER_HEIGHT + MARGIN + PANEL_HEIGHT + MARGIN + 10);
  display.println("GPU");
  
  display.setCursor(MARGIN + PANEL_WIDTH + MARGIN + 10, HEADER_HEIGHT + MARGIN + PANEL_HEIGHT + MARGIN + 10);
  display.println("SYSTEM");
  
  display.setCursor(MARGIN + 2 * (PANEL_WIDTH + MARGIN) + 10, HEADER_HEIGHT + MARGIN + PANEL_HEIGHT + MARGIN + 10);
  display.println("TEMPS");
  
  display.setCursor(MARGIN + 3 * (PANEL_WIDTH + MARGIN) + 10, HEADER_HEIGHT + MARGIN + PANEL_HEIGHT + MARGIN + 10);
  display.println("STATUS");
}

void updateDisplay() {
  if (!telemetry.data_valid) {
    return;
  }
  
  // Update header
  drawHeader();
  
  // Update panels
  updateCPUPanel();
  updateMemoryPanel();
  updateDiskPanel();
  updateNetworkPanel();
  updateGPUPanel();
  updateSystemPanel();
  updateTemperaturePanel();
  updateStatusPanel();
}

void updateCPUPanel() {
  int x = MARGIN;
  int y = HEADER_HEIGHT + MARGIN;
  
  // Clear data area
  display.fillRect(x + 2, y + 30, PANEL_WIDTH - 4, PANEL_HEIGHT - 32, BLACK);
  
  // CPU Usage
  display.setTextSize(3);
  display.setTextColor(getColorForPercentage(telemetry.cpu_usage));
  display.setCursor(x + 10, y + 40);
  display.print(telemetry.cpu_usage, 1);
  display.println("%");
  
  // CPU Frequency
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(x + 10, y + 80);
  display.print(telemetry.cpu_frequency, 0);
  display.println(" MHz");
  
  // CPU Cores
  display.setCursor(x + 10, y + 95);
  display.print("Cores: ");
  display.println(telemetry.cpu_cores);
  
  // Progress bar
  drawProgressBar(x + 10, y + 110, PANEL_WIDTH - 20, 15, telemetry.cpu_usage);
}

void updateMemoryPanel() {
  int x = MARGIN + PANEL_WIDTH + MARGIN;
  int y = HEADER_HEIGHT + MARGIN;
  
  // Clear data area
  display.fillRect(x + 2, y + 30, PANEL_WIDTH - 4, PANEL_HEIGHT - 32, BLACK);
  
  // Memory Usage
  display.setTextSize(3);
  display.setTextColor(getColorForPercentage(telemetry.memory_usage_percent));
  display.setCursor(x + 10, y + 40);
  display.print(telemetry.memory_usage_percent, 1);
  display.println("%");
  
  // Memory details
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(x + 10, y + 80);
  display.print("Used: ");
  display.print(telemetry.memory_used_gb, 1);
  display.println(" GB");
  
  display.setCursor(x + 10, y + 95);
  display.print("Total: ");
  display.print(telemetry.memory_total_gb, 1);
  display.println(" GB");
  
  // Progress bar
  drawProgressBar(x + 10, y + 110, PANEL_WIDTH - 20, 15, telemetry.memory_usage_percent);
}

void updateDiskPanel() {
  int x = MARGIN + 2 * (PANEL_WIDTH + MARGIN);
  int y = HEADER_HEIGHT + MARGIN;
  
  // Clear data area
  display.fillRect(x + 2, y + 30, PANEL_WIDTH - 4, PANEL_HEIGHT - 32, BLACK);
  
  // Read Speed
  display.setTextSize(2);
  display.setTextColor(GREEN);
  display.setCursor(x + 10, y + 40);
  display.print("R: ");
  display.print(telemetry.disk_read_speed, 1);
  display.println(" MB/s");
  
  // Write Speed
  display.setTextColor(ORANGE);
  display.setCursor(x + 10, y + 65);
  display.print("W: ");
  display.print(telemetry.disk_write_speed, 1);
  display.println(" MB/s");
  
  // Disk Usage
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(x + 10, y + 95);
  display.print("Usage: ");
  display.print(telemetry.disk_usage_percent, 1);
  display.println("%");
  
  // Progress bar for disk usage
  drawProgressBar(x + 10, y + 110, PANEL_WIDTH - 20, 15, telemetry.disk_usage_percent);
}

void updateNetworkPanel() {
  int x = MARGIN + 3 * (PANEL_WIDTH + MARGIN);
  int y = HEADER_HEIGHT + MARGIN;
  
  // Clear data area
  display.fillRect(x + 2, y + 30, PANEL_WIDTH - 4, PANEL_HEIGHT - 32, BLACK);
  
  // Upload Speed
  display.setTextSize(2);
  display.setTextColor(CYAN);
  display.setCursor(x + 10, y + 40);
  display.print("UP: ");
  display.print(telemetry.network_upload_speed, 1);
  display.println(" MB/s");
  
  // Download Speed
  display.setTextColor(MAGENTA);
  display.setCursor(x + 10, y + 65);
  display.print("DN: ");
  display.print(telemetry.network_download_speed, 1);
  display.println(" MB/s");
  
  // Network activity indicator
  float total_activity = telemetry.network_upload_speed + telemetry.network_download_speed;
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(x + 10, y + 95);
  display.print("Activity: ");
  display.print(total_activity, 1);
  display.println(" MB/s");
}

void updateGPUPanel() {
  int x = MARGIN;
  int y = HEADER_HEIGHT + MARGIN + PANEL_HEIGHT + MARGIN;
  
  // Clear data area
  display.fillRect(x + 2, y + 30, PANEL_WIDTH - 4, PANEL_HEIGHT - 32, BLACK);
  
  // GPU Usage
  display.setTextSize(3);
  display.setTextColor(getColorForPercentage(telemetry.gpu_usage));
  display.setCursor(x + 10, y + 40);
  display.print(telemetry.gpu_usage, 1);
  display.println("%");
  
  // GPU Memory
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(x + 10, y + 80);
  display.print("Mem: ");
  display.print(telemetry.gpu_memory_percent, 1);
  display.println("%");
  
  // GPU Name (truncated)
  display.setCursor(x + 10, y + 95);
  String truncated_name = telemetry.gpu_name;
  if (truncated_name.length() > 15) {
    truncated_name = truncated_name.substring(0, 15);
  }
  display.println(truncated_name);
  
  // Progress bar
  drawProgressBar(x + 10, y + 110, PANEL_WIDTH - 20, 15, telemetry.gpu_usage);
}

void updateSystemPanel() {
  int x = MARGIN + PANEL_WIDTH + MARGIN;
  int y = HEADER_HEIGHT + MARGIN + PANEL_HEIGHT + MARGIN;
  
  // Clear data area
  display.fillRect(x + 2, y + 30, PANEL_WIDTH - 4, PANEL_HEIGHT - 32, BLACK);
  
  // Platform
  display.setTextSize(2);
  display.setTextColor(YELLOW);
  display.setCursor(x + 10, y + 40);
  display.println(telemetry.platform);
  
  // Uptime
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(x + 10, y + 70);
  display.print("Uptime: ");
  display.print(telemetry.uptime_hours);
  display.print("h ");
  display.print(telemetry.uptime_minutes);
  display.println("m");
  
  // Last update time
  display.setCursor(x + 10, y + 85);
  display.print("Updated: ");
  display.print((millis() - telemetry.last_update) / 1000);
  display.println("s ago");
}

void updateTemperaturePanel() {
  int x = MARGIN + 2 * (PANEL_WIDTH + MARGIN);
  int y = HEADER_HEIGHT + MARGIN + PANEL_HEIGHT + MARGIN;
  
  // Clear data area
  display.fillRect(x + 2, y + 30, PANEL_WIDTH - 4, PANEL_HEIGHT - 32, BLACK);
  
  // CPU Temperature
  display.setTextSize(2);
  display.setTextColor(getColorForTemperature(telemetry.cpu_temperature));
  display.setCursor(x + 10, y + 40);
  display.print("CPU: ");
  display.print(telemetry.cpu_temperature, 1);
  display.println("C");
  
  // GPU Temperature
  display.setTextColor(getColorForTemperature(telemetry.gpu_temperature));
  display.setCursor(x + 10, y + 65);
  display.print("GPU: ");
  display.print(telemetry.gpu_temperature, 1);
  display.println("C");
  
  // Temperature status
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(x + 10, y + 95);
  float max_temp = max(telemetry.cpu_temperature, telemetry.gpu_temperature);
  if (max_temp > 80) {
    display.setTextColor(RED);
    display.println("HOT!");
  } else if (max_temp > 65) {
    display.setTextColor(YELLOW);
    display.println("WARM");
  } else {
    display.setTextColor(GREEN);
    display.println("COOL");
  }
}

void updateStatusPanel() {
  int x = MARGIN + 3 * (PANEL_WIDTH + MARGIN);
  int y = HEADER_HEIGHT + MARGIN + PANEL_HEIGHT + MARGIN;
  
  // Clear data area
  display.fillRect(x + 2, y + 30, PANEL_WIDTH - 4, PANEL_HEIGHT - 32, BLACK);
  
  // Connection status
  display.setTextSize(2);
  unsigned long time_since_update = millis() - telemetry.last_update;
  
  if (time_since_update < 5000) {
    display.setTextColor(GREEN);
    display.setCursor(x + 10, y + 40);
    display.println("ONLINE");
  } else if (time_since_update < 15000) {
    display.setTextColor(YELLOW);
    display.setCursor(x + 10, y + 40);
    display.println("DELAYED");
  } else {
    display.setTextColor(RED);
    display.setCursor(x + 10, y + 40);
    display.println("OFFLINE");
  }
  
  // WiFi status
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(x + 10, y + 70);
  display.print("WiFi: ");
  if (WiFi.status() == WL_CONNECTED) {
    display.setTextColor(GREEN);
    display.println("OK");
  } else {
    display.setTextColor(RED);
    display.println("FAIL");
  }
  
  // IP Address
  display.setTextColor(WHITE);
  display.setCursor(x + 10, y + 85);
  display.print("IP: ");
  String ip = WiFi.localIP().toString();
  if (ip.length() > 12) {
    ip = ip.substring(ip.lastIndexOf('.') - 3);
  }
  display.println(ip);
}

void drawProgressBar(int x, int y, int width, int height, float percentage) {
  // Draw border
  display.drawRect(x, y, width, height, WHITE);
  
  // Fill based on percentage
  int fill_width = (width - 2) * (percentage / 100.0);
  uint16_t fill_color = getColorForPercentage(percentage);
  
  // Clear inside
  display.fillRect(x + 1, y + 1, width - 2, height - 2, BLACK);
  
  // Draw fill
  if (fill_width > 0) {
    display.fillRect(x + 1, y + 1, fill_width, height - 2, fill_color);
  }
}

uint16_t getColorForPercentage(float percentage) {
  if (percentage > 80) return RED;
  if (percentage > 60) return YELLOW;
  return GREEN;
}

uint16_t getColorForTemperature(float temperature) {
  if (temperature > 80) return RED;
  if (temperature > 65) return YELLOW;
  return GREEN;
}

void checkConnectionStatus() {
  // Check if data is stale
  if (telemetry.data_valid && (millis() - telemetry.last_update > 30000)) {
    Serial.println("Data connection timeout");
    // Could implement reconnection logic here
  }
  
  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi connection lost");
    // Could implement WiFi reconnection here
  }
}