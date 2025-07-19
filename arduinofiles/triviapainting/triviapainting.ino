#include <Servo.h>

Servo myservo;

const int buttonPin = 2;
int buttonState = 0;
int pos = 0;

// Relay pins
const int relayPins[3] = {3, 4, 5};

bool inIdleMode = true;

void setup() {
  myservo.attach(9);
  myservo.write(90);
  delay(50);

  Serial.begin(9600);
  pinMode(buttonPin, INPUT_PULLUP);

  for (int i = 0; i < 3; i++) {
    pinMode(relayPins[i], OUTPUT);
    digitalWrite(relayPins[i], HIGH); // all lights OFF initially
  }

  randomSeed(analogRead(A0));
}

void loop() {
  buttonState = digitalRead(buttonPin);
  Serial.println(buttonState);
  if (buttonState==0) {
    runServoSequence();
  }
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input.equalsIgnoreCase("win")) {
      runServoSequence();
    }

    if (input.equalsIgnoreCase("idle")) {
      inIdleMode = true;
    } else if (input == "1" || input == "2" || input == "3"|| input == "0") {
      int count = input.toInt();
      setRelays(count);
      inIdleMode = false;
    }
  }

  if (inIdleMode) {
    runIdleStep();
  }
}

void runServoSequence() {
  Serial.println("Triggered!");
  for (pos = 90; pos >= 0; pos -= 1) {
    myservo.write(pos);
    delay(5);
  }
  for (pos = 0; pos <= 90; pos += 1) {
    Serial.println(pos);
    myservo.write(pos);
    delay(7);
  }
}

void setRelays(int count) {
  for (int i = 0; i < 3; i++) {
    if (i < count) {
      digitalWrite(relayPins[i], LOW); // ON
    } else {
      digitalWrite(relayPins[i], HIGH); // OFF
    }
  }
}

void runIdleStep() {
  for (int i = 0; i < 3; i++) {
    bool on = random(0, 2);
    digitalWrite(relayPins[i], on ? LOW : HIGH);
  }
  delay(450);
}
