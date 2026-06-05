#include <Wire.h>
#include <Adafruit_SHT4x.h>

Adafruit_SHT4x sht4 = Adafruit_SHT4x();

const int RELAY_1V_PIN  = 8;   // IN1
const int RELAY_35V_PIN = 9;   // IN2

// Relay module used in this setup is active LOW.
const bool RELAY_ACTIVE_LOW = true;

const unsigned long READ_INTERVAL_MS = 1000;
const unsigned int RELAY_SWITCH_DELAY_MS = 50;

enum OutputState {
  OUTPUT_0V,
  OUTPUT_1V,
  OUTPUT_35V
};

OutputState currentState = OUTPUT_0V;
unsigned long lastReadTime = 0;

void setRelay(int pin, bool on) {
  if (RELAY_ACTIVE_LOW) {
    digitalWrite(pin, on ? LOW : HIGH);
  } else {
    digitalWrite(pin, on ? HIGH : LOW);
  }
}

void allRelaysOff() {
  setRelay(RELAY_1V_PIN, false);
  setRelay(RELAY_35V_PIN, false);
}

void applyOutputState(OutputState newState) {
  if (newState == currentState) return;

  // Turn both relays off before switching to the next voltage line.
  allRelaysOff();
  delay(RELAY_SWITCH_DELAY_MS);

  switch (newState) {
    case OUTPUT_0V:
      break;

    case OUTPUT_1V:
      setRelay(RELAY_1V_PIN, true);
      break;

    case OUTPUT_35V:
      setRelay(RELAY_35V_PIN, true);
      break;
  }

  currentState = newState;
}

OutputState decideStateFromHumidity(float rh) {
  if (rh < 50.0f) {
    return OUTPUT_0V;
  } else if (rh < 70.0f) {
    return OUTPUT_1V;
  } else {
    return OUTPUT_35V;
  }
}

void setup() {
  Serial.begin(115200);
  Wire.begin();   // Uno R3: A4 = SDA, A5 = SCL

  pinMode(RELAY_1V_PIN, OUTPUT);
  pinMode(RELAY_35V_PIN, OUTPUT);

  allRelaysOff();
  currentState = OUTPUT_0V;

  if (!sht4.begin()) {
    while (1) {
      delay(1000);
    }
  }

  sht4.setPrecision(SHT4X_HIGH_PRECISION);
  sht4.setHeater(SHT4X_NO_HEATER);

  Serial.println("time_s,humidity_rh");
}

void loop() {
  if (millis() - lastReadTime >= READ_INTERVAL_MS) {
    lastReadTime = millis();

    sensors_event_t humidity, temp;

    if (!sht4.getEvent(&humidity, &temp)) {
      applyOutputState(OUTPUT_0V);
      return;
    }

    float rh = humidity.relative_humidity;
    float time_s = millis() / 1000.0f;

    OutputState targetState = decideStateFromHumidity(rh);
    applyOutputState(targetState);

    Serial.print(time_s, 2);
    Serial.print(",");
    Serial.println(rh, 2);
  }
}
