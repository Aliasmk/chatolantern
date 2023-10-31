#include <FastLED.h>


#define WIDTH 20
#define HEIGHT 10
#define NUM_LEDS WIDTH * HEIGHT


#define DATA_PIN 3

// Define the array of leds
CRGB leds[NUM_LEDS];

void setup() { 
    Serial.begin(230400);
    FastLED.addLeds<WS2812B, DATA_PIN>(leds, NUM_LEDS);  // GRB ordering is assumed
    FastLED.setBrightness(20);
    FastLED.clear();
    FastLED.show();

    pinMode(13, OUTPUT);

}

long long int last_serial = 0;

void loop() { 
  int data_length = 0;

  while (data_length < NUM_LEDS * 3){
    int led = data_length / 3;
    int color = data_length % 3;
    if(Serial.available()>0){
      leds[led].raw[color] = (uint8_t)Serial.read();
      data_length++;
      last_serial = millis();
    }

    if(millis() - last_serial > 1000){
      digitalWrite(13, LOW);
      FastLED.clear();
      FastLED.show();
    } else {
      digitalWrite(13, HIGH);
      
    }
  }
  
  FastLED.show();

  // Wait for the start of the next frame
  if(data_length == NUM_LEDS * 3){
    while(Serial.available() > 0){
      Serial.read();
      
    }
  }

  

}