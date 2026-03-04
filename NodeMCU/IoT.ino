#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// ==========================================
// CONFIGURATION
// ==========================================
const char* ssid = "Harsha";
const char* password = "123456789";

// OLED Display Setup
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
// Initialize OLED on standard I2C pins (D1=SCL, D2=SDA)
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// Hardware Pins
#define DHTPIN D7      
#define DHTTYPE DHT11
#define SOIL_POWER_PIN D0  // MOVED TO D0 TO FREE UP I2C
#define SOIL_DATA_PIN A0   
#define LDR_POWER_PIN D5   
#define LDR_DATA_PIN D6    

DHT dht(DHTPIN, DHTTYPE);
ESP8266WebServer server(80);

// Global Variables to hold the latest sensor data
float currentTemp = 0.0;
float currentHum = 0.0;
int currentSoil = 0;
String currentLight = "Unknown";

// Timer Variables
unsigned long previousMillis = 0;
const long interval = 2000; // Update screen and sensors every 2 seconds

void setup() {
  Serial.begin(9600);
  dht.begin();

  // Initialize Pins
  pinMode(SOIL_POWER_PIN, OUTPUT);
  pinMode(LDR_POWER_PIN, OUTPUT);
  pinMode(LDR_DATA_PIN, INPUT);
  digitalWrite(SOIL_POWER_PIN, LOW);
  digitalWrite(LDR_POWER_PIN, LOW);

  // Initialize OLED
  // Address 0x3C is standard for 128x64 I2C OLEDs
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { 
    Serial.println(F("SSD1306 allocation failed"));
    for(;;); // Don't proceed, loop forever
  }
  
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 10);
  display.println("S.A.G.E. Booting...");
  display.display();

  // Connect Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }

  server.on("/data", sendJsonData); 
  server.begin();
}

void loop() {
  // 1. Constantly listen for Streamlit requests
  server.handleClient(); 

  // 2. Non-blocking timer to update sensors and OLED every 2 seconds
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    readSensors();
    updateOLED();
  }
}

void readSensors() {
  // Read DHT
  currentHum = dht.readHumidity();
  currentTemp = dht.readTemperature();

  // Read Soil
  digitalWrite(SOIL_POWER_PIN, HIGH);      
  delay(100);                              
  int soilRaw = analogRead(SOIL_DATA_PIN); 
  digitalWrite(SOIL_POWER_PIN, LOW);       
  currentSoil = constrain(map(soilRaw, 1024, 30, 0, 100), 0, 100);

  // Read LDR
  digitalWrite(LDR_POWER_PIN, HIGH);       
  delay(100);                              
  int isDark = digitalRead(LDR_DATA_PIN);  
  digitalWrite(LDR_POWER_PIN, LOW);        
  currentLight = (isDark == 0) ? "Bright" : "Dark";
}

void updateOLED() {
  display.clearDisplay();
  
  // Header
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.print("IP:");
  display.println(WiFi.localIP());
  display.drawLine(0, 10, 128, 10, SSD1306_WHITE);

  // Sensor Data
  display.setCursor(0, 16);
  display.print("Temp: "); 
  if(isnan(currentTemp)) display.print("ERR"); else display.print(currentTemp);
  display.println(" C");

  display.setCursor(0, 28);
  display.print("Hum:  "); 
  if(isnan(currentHum)) display.print("ERR"); else display.print(currentHum);
  display.println(" %");

  display.setCursor(0, 40);
  display.print("Soil: "); display.print(currentSoil); display.println(" %");

  display.setCursor(0, 52);
  display.print("Sun:  "); display.println(currentLight);

  display.display(); // Push drawing to screen
}

void sendJsonData() {
  // This function is now lightning fast because data is already pre-loaded
  StaticJsonDocument<200> doc;
  
  if (isnan(currentTemp) || isnan(currentHum)) {
    doc["temp"] = "Error";
    doc["humidity"] = "Error";
  } else {
    doc["temp"] = currentTemp;
    doc["humidity"] = currentHum;
  }
  
  doc["soil"] = currentSoil;
  doc["light"] = currentLight;

  String jsonResponse;
  serializeJson(doc, jsonResponse);
  server.send(200, "application/json", jsonResponse);
}