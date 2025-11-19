#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ESP8266mDNS.h>

const char* ssid = "SLT";
const char* password = "PASS";

ESP8266WebServer server(80);

// Pin Configuration for Transistor Control
const int led1Pin = D1;      // Red LED (GPIO5) - Direct with 220Ω resistor
const int led2Pin = D2;      // Green LED (GPIO4) - Direct with 220Ω resistor
const int buzzerPin = D5;    // Buzzer (GPIO14) - Through transistor with 1KΩ base resistor
const int motorPin = D6;     // Motor (GPIO12) - Through transistor with 1KΩ base resistor

// State Tracking
bool led1State = false;
bool led2State = false;

// Track request performance
unsigned long lastPerfLog = 0;
unsigned long requestCount = 0;

void setup() {
  Serial.begin(115200);
  
  pinMode(led1Pin, OUTPUT);
  pinMode(led2Pin, OUTPUT);
  pinMode(buzzerPin, OUTPUT);
  pinMode(motorPin, OUTPUT);
  
  digitalWrite(led1Pin, LOW);
  digitalWrite(led2Pin, LOW);
  digitalWrite(buzzerPin, LOW);
  digitalWrite(motorPin, LOW);
  
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  
  // Setup mDNS for easy discovery
  if (MDNS.begin("esp8266")) {
    Serial.println("mDNS started: http://esp8266.local");
    MDNS.addService("http", "tcp", 80);
  } else {
    Serial.println("Error setting up mDNS!");
  }
  
  // API Endpoints
  server.on("/status", HTTP_GET, [](){
    unsigned long start = millis();
    requestCount++;
    server.send(200, "text/plain", "ESP8266 OK");
    Serial.printf("[DEBUG] /status - %lums\n", millis() - start);
  });
  
  server.on("/led1_toggle", HTTP_GET, [](){
    unsigned long start = millis();
    requestCount++;
    led1State = !led1State;
    digitalWrite(led1Pin, led1State ? HIGH : LOW);
    server.send(200, "text/plain", led1State ? "LED1 ON" : "LED1 OFF");
    Serial.printf("[DEBUG] /led1_toggle -> %s - %lums\n", led1State ? "ON" : "OFF", millis() - start);
  });
  
  server.on("/led2_toggle", HTTP_GET, [](){
    unsigned long start = millis();
    requestCount++;
    led2State = !led2State;
    digitalWrite(led2Pin, led2State ? HIGH : LOW);
    server.send(200, "text/plain", led2State ? "LED2 ON" : "LED2 OFF");
    Serial.printf("[DEBUG] /led2_toggle -> %s - %lums\n", led2State ? "ON" : "OFF", millis() - start);
  });
  
  server.on("/led1/on", HTTP_GET, [](){
    unsigned long start = millis();
    requestCount++;
    digitalWrite(led1Pin, HIGH);
    server.send(200, "text/plain", "LED1 ON");
    Serial.printf("[DEBUG] /led1/on - %lums\n", millis() - start);
  });
  
  server.on("/led1/off", HTTP_GET, [](){
    unsigned long start = millis();
    requestCount++;
    digitalWrite(led1Pin, LOW);
    server.send(200, "text/plain", "LED1 OFF");
    Serial.printf("[DEBUG] /led1/off - %lums\n", millis() - start);
  });
  
  server.on("/led2/on", HTTP_GET, [](){
    unsigned long start = millis();
    requestCount++;
    digitalWrite(led2Pin, HIGH);
    server.send(200, "text/plain", "LED2 ON");
    Serial.printf("[DEBUG] /led2/on - %lums\n", millis() - start);
  });
  
  server.on("/led2/off", HTTP_GET, [](){
    unsigned long start = millis();
    requestCount++;
    digitalWrite(led2Pin, LOW);
    server.send(200, "text/plain", "LED2 OFF");
    Serial.printf("[DEBUG] /led2/off - %lums\n", millis() - start);
  });
  
  server.on("/buzzer/on", HTTP_GET, [](){
    unsigned long start = millis();
    requestCount++;
    digitalWrite(buzzerPin, HIGH);
    server.send(200, "text/plain", "Buzzer ON");
    Serial.printf("[DEBUG] /buzzer/on - %lums\n", millis() - start);
  });
  
  server.on("/buzzer/off", HTTP_GET, [](){
    unsigned long start = millis();
    requestCount++;
    digitalWrite(buzzerPin, LOW);
    server.send(200, "text/plain", "Buzzer OFF");
    Serial.printf("[DEBUG] /buzzer/off - %lums\n", millis() - start);
  });
  
  server.on("/motor/on", HTTP_GET, [](){
    unsigned long start = millis();
    requestCount++;
    digitalWrite(motorPin, HIGH);  // Turn on transistor
    server.send(200, "text/plain", "Motor ON");
    Serial.printf("[DEBUG] /motor/on - %lums\n", millis() - start);
  });
  
  server.on("/motor/off", HTTP_GET, [](){
    unsigned long start = millis();
    requestCount++;
    digitalWrite(motorPin, LOW);  // Turn off transistor
    server.send(200, "text/plain", "Motor OFF");
    Serial.printf("[DEBUG] /motor/off - %lums\n", millis() - start);
  });
  
  // Batch control endpoint - handle multiple commands in one request
  // Usage: /batch?led1=on&led2=off&motor=on&buzzer=off
  server.on("/batch", HTTP_GET, [](){
    unsigned long start = millis();
    requestCount++;
    
    String response = "Batch: ";
    int commandCount = 0;
    
    // Control LED1
    if (server.hasArg("led1")) {
      String value = server.arg("led1");
      if (value == "on") {
        digitalWrite(led1Pin, HIGH);
        response += "LED1=ON ";
      } else if (value == "off") {
        digitalWrite(led1Pin, LOW);
        response += "LED1=OFF ";
      }
      commandCount++;
    }
    
    // Control LED2
    if (server.hasArg("led2")) {
      String value = server.arg("led2");
      if (value == "on") {
        digitalWrite(led2Pin, HIGH);
        response += "LED2=ON ";
      } else if (value == "off") {
        digitalWrite(led2Pin, LOW);
        response += "LED2=OFF ";
      }
      commandCount++;
    }
    
    // Control Buzzer
    if (server.hasArg("buzzer")) {
      String value = server.arg("buzzer");
      if (value == "on") {
        digitalWrite(buzzerPin, HIGH);
        response += "BUZZER=ON ";
      } else if (value == "off") {
        digitalWrite(buzzerPin, LOW);
        response += "BUZZER=OFF ";
      }
      commandCount++;
    }
    
    // Control Motor
    if (server.hasArg("motor")) {
      String value = server.arg("motor");
      if (value == "on") {
        digitalWrite(motorPin, HIGH);
        response += "MOTOR=ON ";
      } else if (value == "off") {
        digitalWrite(motorPin, LOW);
        response += "MOTOR=OFF ";
      }
      commandCount++;
    }
    
    server.send(200, "text/plain", response);
    Serial.printf("[DEBUG] /batch (%d commands) - %lums\n", commandCount, millis() - start);
  });
  
  server.begin();
  Serial.println("HTTP server started");
}

void loop() {
  server.handleClient();
  MDNS.update();  // Keep mDNS alive
  
  // Log WiFi signal strength every 10 seconds
  if (millis() - lastPerfLog > 10000) {
    int rssi = WiFi.RSSI();
    Serial.printf("\n[WIFI] Signal: %d dBm | Requests: %lu\n", rssi, requestCount);
    if (rssi < -80) {
      Serial.println("[WARNING] Weak WiFi signal - may cause delays!");
    }
    lastPerfLog = millis();
    requestCount = 0;
  }
  
  yield();
}
