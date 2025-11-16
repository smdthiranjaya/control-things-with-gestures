// Simple LED Test Sketch for ESP8266
// Upload this first to test your LED connections

#include <ESP8266WiFi.h>

const char* ssid = "SLT";          // Change to your WiFi name
const char* password = "PASS";      // Change to your WiFi password

// Pin definitions (matching the wiring diagram)
const int led1Pin = D1;  // GPIO 5
const int led2Pin = D2;  // GPIO 4
const int led3Pin = D3;  // GPIO 0

void setup() {
  Serial.begin(115200);
  Serial.println("\n\nESP8266 LED Test Starting...");
  
  // Setup LED pins
  pinMode(led1Pin, OUTPUT);
  pinMode(led2Pin, OUTPUT);
  pinMode(led3Pin, OUTPUT);
  
  // Turn all LEDs off initially
  digitalWrite(led1Pin, LOW);
  digitalWrite(led2Pin, LOW);
  digitalWrite(led3Pin, LOW);
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✓ WiFi Connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.println("\nUpdate this IP in your Python config.py:");
    Serial.print("  esp8266_ip: \"");
    Serial.print(WiFi.localIP());
    Serial.println("\"");
  } else {
    Serial.println("\n✗ WiFi Connection Failed!");
    Serial.println("Check your SSID and Password");
  }
  
  Serial.println("\nStarting LED Test Sequence...");
}

void loop() {
  // Test sequence: Blink each LED one by one
  
  Serial.println("LED1 ON");
  digitalWrite(led1Pin, HIGH);
  delay(1000);
  digitalWrite(led1Pin, LOW);
  delay(500);
  
  Serial.println("LED2 ON");
  digitalWrite(led2Pin, HIGH);
  delay(1000);
  digitalWrite(led2Pin, LOW);
  delay(500);
  
  Serial.println("LED3 ON");
  digitalWrite(led3Pin, HIGH);
  delay(1000);
  digitalWrite(led3Pin, LOW);
  delay(500);
  
  Serial.println("All LEDs ON");
  digitalWrite(led1Pin, HIGH);
  digitalWrite(led2Pin, HIGH);
  digitalWrite(led3Pin, HIGH);
  delay(1000);
  
  Serial.println("All LEDs OFF");
  digitalWrite(led1Pin, LOW);
  digitalWrite(led2Pin, LOW);
  digitalWrite(led3Pin, LOW);
  delay(2000);
  
  Serial.println("---");
}
