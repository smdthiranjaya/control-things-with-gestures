#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>

const char* ssid = "SLT";
const char* password = "PASS";

ESP8266WebServer server(80);

// Pin Configuration
const int led1Pin = D1;
const int led2Pin = D2;
const int led3Pin = D3;
const int motorPin = D4;
const int fingerMotorPin = D5;
const int handMotorPin = D6;
const int bulbPin = D7;

// PWM Configuration
const int pwmFrequency = 1000;
const int pwmRange = 1023;

// State Tracking
bool led1State = false;
bool led2State = false;

void setup() {
  Serial.begin(115200);
  
  pinMode(led1Pin, OUTPUT);
  pinMode(led2Pin, OUTPUT);
  pinMode(led3Pin, OUTPUT);
  pinMode(motorPin, OUTPUT);
  pinMode(fingerMotorPin, OUTPUT);
  pinMode(handMotorPin, OUTPUT);
  pinMode(bulbPin, OUTPUT);
  
  digitalWrite(led1Pin, LOW);
  digitalWrite(led2Pin, LOW);
  digitalWrite(led3Pin, LOW);
  digitalWrite(motorPin, LOW);
  
  analogWriteRange(pwmRange);
  analogWriteFreq(pwmFrequency);
  analogWrite(fingerMotorPin, 0);
  analogWrite(handMotorPin, 0);
  analogWrite(bulbPin, 0);
  
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
  
  server.on("/led3/on", HTTP_GET, [](){
    digitalWrite(led3Pin, HIGH);
    server.send(200, "text/plain", "LED3 ON");
  });
  
  server.on("/led3/off", HTTP_GET, [](){
    digitalWrite(led3Pin, LOW);
    server.send(200, "text/plain", "LED3 OFF");
  });
  
  server.on("/motor/on", HTTP_GET, [](){
    digitalWrite(motorPin, HIGH);
    server.send(200, "text/plain", "Motor ON");
  });
  
  server.on("/motor/off", HTTP_GET, [](){
    digitalWrite(motorPin, LOW);
    server.send(200, "text/plain", "Motor OFF");
  });
  
  server.on("/finger_motor/on", HTTP_GET, [](){
    analogWrite(fingerMotorPin, pwmRange);
    server.send(200, "text/plain", "Finger Motor ON");
  });
  
  server.on("/finger_motor/off", HTTP_GET, [](){
    analogWrite(fingerMotorPin, 0);
    server.send(200, "text/plain", "Finger Motor OFF");
  });
  
  server.on("/finger_motor/set", HTTP_GET, [](){
    String path = server.uri();
    int lastSlash = path.lastIndexOf('/');
    if (lastSlash != -1 && lastSlash < path.length() - 1) {
      String valueStr = path.substring(lastSlash + 1);
      int value = valueStr.toInt();
      value = constrain(value, 0, 100);
      int pwmValue = map(value, 0, 100, 0, pwmRange);
      analogWrite(fingerMotorPin, pwmValue);
      server.send(200, "text/plain", "Finger Motor: " + String(value) + "%");
    } else {
      server.send(400, "text/plain", "Invalid request");
    }
  });
  
  server.on("/hand_motor/on", HTTP_GET, [](){
    analogWrite(handMotorPin, pwmRange); 
    server.send(200, "text/plain", "Hand Motor ON");
  });
  
  server.on("/hand_motor/off", HTTP_GET, [](){
    analogWrite(handMotorPin, 0);
    server.send(200, "text/plain", "Hand Motor OFF");
  });
  
  // Update the URL pattern for hand motor with set command
  server.on("/hand_motor/set", HTTP_GET, [](){
    String path = server.uri();
    int lastSlash = path.lastIndexOf('/');
    if (lastSlash != -1 && lastSlash < path.length() - 1) {
      String valueStr = path.substring(lastSlash + 1);
      int value = valueStr.toInt();
      value = constrain(value, 0, 100);
      int pwmValue = map(value, 0, 100, 0, pwmRange);
      analogWrite(handMotorPin, pwmValue);
      server.send(200, "text/plain", "Hand Motor: " + String(value) + "%");
    } else {
      server.send(400, "text/plain", "Invalid request");
    }
  });
  
  // Routes for bulb control
  server.on("/bulb/on", HTTP_GET, [](){
    analogWrite(bulbPin, pwmRange);
    server.send(200, "text/plain", "Bulb ON");
  });
  
  server.on("/bulb/off", HTTP_GET, [](){
    analogWrite(bulbPin, 0);
    server.send(200, "text/plain", "Bulb OFF");
  });
  
  server.on("/bulb/set", HTTP_GET, [](){
    String path = server.uri();
    int lastSlash = path.lastIndexOf('/');
    if (lastSlash != -1 && lastSlash < path.length() - 1) {
      String valueStr = path.substring(lastSlash + 1);
      int value = valueStr.toInt();
      value = constrain(value, 0, 100);
      int pwmValue = map(value, 0, 100, 0, pwmRange);
      analogWrite(bulbPin, pwmValue);
      server.send(200, "text/plain", "Bulb: " + String(value) + "%");
    } else {
      server.send(400, "text/plain", "Invalid request");
    }
  });
  
  // Register handler for URLs with parameters
  server.onNotFound([](){
    String path = server.uri();
    
    if (path.startsWith("/finger_motor/set/")) {
      String valueStr = path.substring(18);
      int value = valueStr.toInt();
      value = constrain(value, 0, 100);
      int pwmValue = map(value, 0, 100, 0, pwmRange);
      analogWrite(fingerMotorPin, pwmValue);
      server.send(200, "text/plain", "Finger Motor: " + String(value) + "%");
      return;
    }
    
    if (path.startsWith("/hand_motor/set/")) {
      String valueStr = path.substring(16);
      int value = valueStr.toInt();
      value = constrain(value, 0, 100);
      int pwmValue = map(value, 0, 100, 0, pwmRange);
      analogWrite(handMotorPin, pwmValue);
      server.send(200, "text/plain", "Hand Motor: " + String(value) + "%");
      return;
    }
    
    if (path.startsWith("/bulb/set/")) {
      String valueStr = path.substring(10);
      int value = valueStr.toInt();
      value = constrain(value, 0, 100);
      int pwmValue = map(value, 0, 100, 0, pwmRange);
      analogWrite(bulbPin, pwmValue);
      server.send(200, "text/plain", "Bulb: " + String(value) + "%");
      return;
    }
    
    server.send(404, "text/plain", "Not Found");
  });
  
  server.begin();
  Serial.println("HTTP server started");
}

void loop() {
  server.handleClient();
  yield();
}
