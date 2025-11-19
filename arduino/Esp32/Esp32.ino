#include <WiFi.h>
#include <WebServer.h>

const char* ssid = "SLT";
const char* password = "PASS";

WebServer server(80);

// Pin Configuration
const int led1Pin = 5;       // Red LED
const int led2Pin = 18;      // Green LED
const int buzzerPin = 19;    // Buzzer
const int motorPin = 21;     // Motor

// State Tracking
bool led1State = false;
bool led2State = false;

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
  
  // API Endpoints
  server.on("/status", HTTP_GET, [](){
    server.send(200, "text/plain", "ESP32 OK");
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
    digitalWrite(motorPin, HIGH);
    server.send(200, "text/plain", "Motor ON");
  });
  
  server.on("/motor/off", HTTP_GET, [](){
    digitalWrite(motorPin, LOW);
    server.send(200, "text/plain", "Motor OFF");
  });
  
  server.begin();
  Serial.println("HTTP server started");
}

void loop() {
  server.handleClient();
  delay(2);
}
