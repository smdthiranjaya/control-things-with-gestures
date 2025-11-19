#include "esp_camera.h"
#include <WiFi.h>
#include <EEPROM.h>
#include <ESPmDNS.h>
#include <WebServer.h>

// EEPROM addresses for WiFi credentials
#define EEPROM_SIZE 512
#define SSID_ADDR 0
#define PASS_ADDR 100

//
// WARNING!!! PSRAM IC required for UXGA resolution and high JPEG quality
//            Ensure ESP32 Wrover Module or other board with PSRAM is selected
//            Partial images will be transmitted if image exceeds buffer size
//
//            You must select partition scheme from the board menu that has at least 3MB APP space.
//            Face Recognition is DISABLED for ESP32 and ESP32-S2, because it takes up from 15
//            seconds to process single frame. Face Detection is ENABLED if PSRAM is enabled as well

// ===================
// Select camera model
// ===================
//#define CAMERA_MODEL_WROVER_KIT // Has PSRAM
#define CAMERA_MODEL_AI_THINKER  // Has PSRAM
//#define CAMERA_MODEL_ESP32S3_EYE // Has PSRAM
//#define CAMERA_MODEL_M5STACK_PSRAM // Has PSRAM
//#define CAMERA_MODEL_M5STACK_V2_PSRAM // M5Camera version B Has PSRAM
//#define CAMERA_MODEL_M5STACK_WIDE // Has PSRAM
//#define CAMERA_MODEL_M5STACK_ESP32CAM // No PSRAM
//#define CAMERA_MODEL_M5STACK_UNITCAM // No PSRAM
//#define CAMERA_MODEL_M5STACK_CAMS3_UNIT  // Has PSRAM
//#define CAMERA_MODEL_AI_THINKER // Has PSRAM
//#define CAMERA_MODEL_TTGO_T_JOURNAL // No PSRAM
//#define CAMERA_MODEL_XIAO_ESP32S3 // Has PSRAM
// ** Espressif Internal Boards **
//#define CAMERA_MODEL_ESP32_CAM_BOARD
//#define CAMERA_MODEL_ESP32S2_CAM_BOARD
//#define CAMERA_MODEL_ESP32S3_CAM_LCD
//#define CAMERA_MODEL_DFRobot_FireBeetle2_ESP32S3 // Has PSRAM
//#define CAMERA_MODEL_DFRobot_Romeo_ESP32S3 // Has PSRAM
#include "camera_pins.h"

// ===========================
// WiFi credentials (loaded from EEPROM or defaults)
// ===========================
String ssid = "SLT";
String password = "PASS";

// AP mode credentials (if WiFi connection fails)
const char* ap_ssid = "ESP32CAM-Setup";
const char* ap_password = "12345678";

void startCameraServer();
void setupLedFlash(int pin);
void setupWiFiEndpoints();
void loadWiFiCredentials();
void saveWiFiCredentials(String newSSID, String newPassword);
void startAPMode();

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.frame_size = FRAMESIZE_UXGA;
  config.pixel_format = PIXFORMAT_JPEG;  // for streaming
  //config.pixel_format = PIXFORMAT_RGB565; // for face detection/recognition
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 12;
  config.fb_count = 1;

  // if PSRAM IC present, init with UXGA resolution and higher JPEG quality
  //                      for larger pre-allocated frame buffer.
  if (config.pixel_format == PIXFORMAT_JPEG) {
    if (psramFound()) {
      config.jpeg_quality = 10;
      config.fb_count = 2;
      config.grab_mode = CAMERA_GRAB_LATEST;
    } else {
      // Limit the frame size when PSRAM is not available
      config.frame_size = FRAMESIZE_SVGA;
      config.fb_location = CAMERA_FB_IN_DRAM;
    }
  } else {
    // Best option for face detection/recognition
    config.frame_size = FRAMESIZE_240X240;
#if CONFIG_IDF_TARGET_ESP32S3
    config.fb_count = 2;
#endif
  }

#if defined(CAMERA_MODEL_AI_THINKER)
  pinMode(13, INPUT_PULLUP);
  pinMode(14, INPUT_PULLUP);
#endif

  // camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  sensor_t *s = esp_camera_sensor_get();
  // initial sensors are flipped vertically and colors are a bit saturated
  if (s->id.PID == OV3660_PID) {
    s->set_vflip(s, 1);        // flip it back
    s->set_brightness(s, 1);   // up the brightness just a bit
    s->set_saturation(s, -2);  // lower the saturation
  }
  // drop down frame size for higher initial frame rate
  if (config.pixel_format == PIXFORMAT_JPEG) {
    s->set_framesize(s, FRAMESIZE_QVGA);
  }

#if defined(CAMERA_MODEL_M5STACK_WIDE) || defined(CAMERA_MODEL_M5STACK_ESP32CAM)
  s->set_vflip(s, 1);
  s->set_hmirror(s, 1);
#endif

#if defined(CAMERA_MODEL_ESP32S3_EYE)
  s->set_vflip(s, 1);
#endif

// Setup LED FLash if LED pin is defined in camera_pins.h
#if defined(LED_GPIO_NUM)
  setupLedFlash(LED_GPIO_NUM);
#endif

  // Initialize EEPROM and load WiFi credentials
  EEPROM.begin(EEPROM_SIZE);
  loadWiFiCredentials();
  
  Serial.println("\nConnecting to WiFi...");
  Serial.print("SSID: ");
  Serial.println(ssid);
  
  WiFi.setSleep(false);
  WiFi.begin(ssid.c_str(), password.c_str());
  
  // Try to connect for 20 seconds
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 40) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("");
    Serial.println("WiFi connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Stream URL: http://");
    Serial.print(WiFi.localIP());
    Serial.println("/stream");
    
    // Setup mDNS for easy discovery
    if (MDNS.begin("esp32cam")) {
      Serial.println("mDNS started: http://esp32cam.local");
      Serial.println("Stream URL: http://esp32cam.local/stream");
      MDNS.addService("http", "tcp", 80);
    }
  } else {
    Serial.println("");
    Serial.println("WiFi connection failed! Starting AP mode...");
    startAPMode();
  }

  startCameraServer();
  setupWiFiEndpoints();

  Serial.println("\n=================================");
  Serial.println("ESP32-CAM Ready!");
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("Camera URL: http://");
    Serial.println(WiFi.localIP());
    Serial.print("Stream URL: http://");
    Serial.print(WiFi.localIP());
    Serial.println("/stream");
    Serial.println("mDNS: http://esp32cam.local");
  } else {
    Serial.println("AP Mode Active");
    Serial.print("Connect to: ");
    Serial.println(ap_ssid);
    Serial.print("Password: ");
    Serial.println(ap_password);
    Serial.print("Configure at: http://");
    Serial.println(WiFi.softAPIP());
  }
  Serial.println("=================================");
}

void loop() {
  // Do nothing. Everything is done in another task by the web server
  delay(10000);
}

// ===========================
// WiFi Management Functions
// ===========================

void loadWiFiCredentials() {
  char ssidBuf[32];
  char passBuf[64];
  
  for (int i = 0; i < 32; i++) {
    ssidBuf[i] = EEPROM.read(SSID_ADDR + i);
    if (ssidBuf[i] == 0) break;
  }
  ssidBuf[31] = 0;
  
  for (int i = 0; i < 64; i++) {
    passBuf[i] = EEPROM.read(PASS_ADDR + i);
    if (passBuf[i] == 0) break;
  }
  passBuf[63] = 0;
  
  // Only use EEPROM values if they look valid
  if (ssidBuf[0] != 0 && ssidBuf[0] != 255) {
    ssid = String(ssidBuf);
    password = String(passBuf);
    Serial.println("Loaded WiFi credentials from EEPROM");
  } else {
    Serial.println("No saved WiFi credentials, using defaults");
  }
}

void saveWiFiCredentials(String newSSID, String newPassword) {
  Serial.println("Saving WiFi credentials to EEPROM...");
  
  // Write SSID
  for (int i = 0; i < newSSID.length(); i++) {
    EEPROM.write(SSID_ADDR + i, newSSID[i]);
  }
  EEPROM.write(SSID_ADDR + newSSID.length(), 0);
  
  // Write Password
  for (int i = 0; i < newPassword.length(); i++) {
    EEPROM.write(PASS_ADDR + i, newPassword[i]);
  }
  EEPROM.write(PASS_ADDR + newPassword.length(), 0);
  
  EEPROM.commit();
  Serial.println("WiFi credentials saved!");
}

void startAPMode() {
  WiFi.mode(WIFI_AP);
  WiFi.softAP(ap_ssid, ap_password);
  
  Serial.println("AP Mode Started");
  Serial.print("AP SSID: ");
  Serial.println(ap_ssid);
  Serial.print("AP Password: ");
  Serial.println(ap_password);
  Serial.print("AP IP Address: ");
  Serial.println(WiFi.softAPIP());
}

void setupWiFiEndpoints() {
  // This requires access to the WebServer from app_httpd.cpp
  // We'll add endpoints there instead
  Serial.println("WiFi endpoints will be added to camera server");
}
