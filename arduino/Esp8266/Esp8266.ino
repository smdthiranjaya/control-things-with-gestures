#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <EEPROM.h>

// Default WiFi credentials (change via web interface)
String ssid = "SLT";
String password = "PASS";

ESP8266WebServer server(80);

// EEPROM addresses
#define EEPROM_SIZE 512
#define SSID_ADDR 0
#define PASS_ADDR 100

// Pin Configuration for Transistor Control
const int led1Pin = D1;      // Red LED (GPIO5) - Direct with 220Ω resistor
const int led2Pin = D2;      // Green LED (GPIO4) - Direct with 220Ω resistor
const int buzzerPin = D5;    // Buzzer (GPIO14) - Through transistor with 1KΩ base resistor
const int motorPin = D6;     // Motor (GPIO12) - Through transistor with 1KΩ base resistor

// State Tracking
bool led1State = false;
bool led2State = false;

void setup() {
  Serial.begin(115200);
  EEPROM.begin(EEPROM_SIZE);
  
  pinMode(led1Pin, OUTPUT);
  pinMode(led2Pin, OUTPUT);
  pinMode(buzzerPin, OUTPUT);
  pinMode(motorPin, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);
  
  digitalWrite(led1Pin, LOW);
  digitalWrite(led2Pin, LOW);
  digitalWrite(buzzerPin, LOW);
  digitalWrite(motorPin, LOW);
  
  // Load WiFi credentials from EEPROM
  loadWiFiCredentials();
  
  // Try to connect to WiFi
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid.c_str(), password.c_str());
  
  Serial.println("\nConnecting to WiFi: " + ssid);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN)); // Blink during connect
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    digitalWrite(LED_BUILTIN, LOW); // LED off when connected
  } else {
    Serial.println("\nWiFi connection failed! Starting AP mode...");
    startAPMode();
  }
  
  // API Endpoints
  server.on("/status", HTTP_GET, [](){
    server.send(200, "text/plain", "ESP8266 OK");
  });
  
  server.on("/led1_toggle", HTTP_GET, [](){
    led1State = !led1State;
    digitalWrite(led1Pin, led1State ? HIGH : LOW);
    server.send(200, "text/plain", led1State ? "LED1 ON" : "LED1 OFF");
  });
  
  server.on("/led2_toggle", HTTP_GET, [](){
    led2State = !led2State;
    digitalWrite(led2Pin, led2State ? HIGH : LOW);
    server.send(200, "text/plain", led2State ? "LED2 ON" : "LED2 OFF");
  });
  
  server.on("/led1/on", HTTP_GET, [](){
    digitalWrite(led1Pin, HIGH);
    server.send(200, "text/plain", "LED1 ON");
  });
  
  server.on("/led1/off", HTTP_GET, [](){
    digitalWrite(led1Pin, LOW);
    server.send(200, "text/plain", "LED1 OFF");
  });
  
  server.on("/led2/on", HTTP_GET, [](){
    digitalWrite(led2Pin, HIGH);
    server.send(200, "text/plain", "LED2 ON");
  });
  
  server.on("/led2/off", HTTP_GET, [](){
    digitalWrite(led2Pin, LOW);
    server.send(200, "text/plain", "LED2 OFF");
  });
  
  server.on("/buzzer/on", HTTP_GET, [](){
    digitalWrite(buzzerPin, HIGH);
    server.send(200, "text/plain", "Buzzer ON");
  });
  
  server.on("/buzzer/off", HTTP_GET, [](){
    digitalWrite(buzzerPin, LOW);
    server.send(200, "text/plain", "Buzzer OFF");
  });
  
  server.on("/motor/on", HTTP_GET, [](){
    digitalWrite(motorPin, HIGH);  // Turn on transistor
    server.send(200, "text/plain", "Motor ON");
  });
  
  server.on("/motor/off", HTTP_GET, [](){
    digitalWrite(motorPin, LOW);  // Turn off transistor
    server.send(200, "text/plain", "Motor OFF");
  });
  
  // WiFi info endpoint
  server.on("/wifi/info", HTTP_GET, [](){
    String json = "{";
    json += "\"ssid\":\"" + WiFi.SSID() + "\",";
    json += "\"ip\":\"" + WiFi.localIP().toString() + "\",";
    json += "\"rssi\":" + String(WiFi.RSSI()) + ",";
    json += "\"mac\":\"" + WiFi.macAddress() + "\"";
    json += "}";
    server.send(200, "application/json", json);
  });
  
  // WiFi scan endpoint
  server.on("/wifi/scan", HTTP_GET, [](){
    int n = WiFi.scanNetworks();
    String json = "[";
    for (int i = 0; i < n; i++) {
      if (i > 0) json += ",";
      json += "{\"ssid\":\"" + WiFi.SSID(i) + "\",";
      json += "\"rssi\":" + String(WiFi.RSSI(i)) + ",";
      json += "\"secure\":" + String(WiFi.encryptionType(i) != ENC_TYPE_NONE) + "}";
    }
    json += "]";
    server.send(200, "application/json", json);
  });
  
  // WiFi configure endpoint
  server.on("/wifi/configure", HTTP_POST, [](){
    if (server.hasArg("ssid") && server.hasArg("password")) {
      String newSSID = server.arg("ssid");
      String newPassword = server.arg("password");
      
      saveWiFiCredentials(newSSID, newPassword);
      
      server.send(200, "text/plain", "WiFi configured! Restarting...");
      delay(1000);
      ESP.restart();
    } else {
      server.send(400, "text/plain", "Missing ssid or password");
    }
  });
  
  server.begin();
  Serial.println("HTTP server started");
}

void startAPMode() {
  WiFi.mode(WIFI_AP);
  WiFi.softAP("ESP8266-Setup", "12345678");
  Serial.println("AP Mode started");
  Serial.print("AP IP: ");
  Serial.println(WiFi.softAPIP());
  digitalWrite(LED_BUILTIN, HIGH); // LED on in AP mode
}

void loadWiFiCredentials() {
  char ssidBuf[32];
  char passBuf[64];
  
  for (int i = 0; i < 32; i++) {
    ssidBuf[i] = EEPROM.read(SSID_ADDR + i);
    if (ssidBuf[i] == 0) break;
  }
  for (int i = 0; i < 64; i++) {
    passBuf[i] = EEPROM.read(PASS_ADDR + i);
    if (passBuf[i] == 0) break;
  }
  
  if (ssidBuf[0] != 0 && ssidBuf[0] != 255) {
    ssid = String(ssidBuf);
    password = String(passBuf);
    Serial.println("Loaded WiFi from EEPROM: " + ssid);
  }
}

void saveWiFiCredentials(String newSSID, String newPassword) {
  for (int i = 0; i < 32; i++) {
    if (i < newSSID.length()) {
      EEPROM.write(SSID_ADDR + i, newSSID[i]);
    } else {
      EEPROM.write(SSID_ADDR + i, 0);
    }
  }
  for (int i = 0; i < 64; i++) {
    if (i < newPassword.length()) {
      EEPROM.write(PASS_ADDR + i, newPassword[i]);
    } else {
      EEPROM.write(PASS_ADDR + i, 0);
    }
  }
  EEPROM.commit();
  Serial.println("WiFi credentials saved to EEPROM");
}

void loop() {
  server.handleClient();
  yield();
}
