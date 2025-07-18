#include <Arduino.h>
#include "ServoEasing.hpp"

ServoEasing servo; 

// IMPORTANT: Mechcnically Disconnect Servo From Eye Before Running The Script
// Upload Code, Write Servo to 90, then connect

// CHANGE THIS to select which servo you want to move manually
int servoPin =4;


// Make a note of the servo min - max and centre positions here, or on some paper
// You can delete my recordings below

//LEFT CENTER RIGHT
// VRight RL Centre/Min/Max 60/95/120 (Pin 3)
// V Right Blink Close/Open 60/85 (Pin 6)

// Left RL Centre/Min/Max 65/95/130 (Pin 10)
// Left Blink Open/Close 80/145 (Pin 4)

// Left UD Centre/Min/Max 45/75/120 (Pin 9)

// Right UD Centre/Min/Max 45/90/120 (Pin 5)

int targetPos;
const int speed = 60;

void setup() {
  Serial.begin(9600);

  servo.attach(servoPin);

  Serial.println("Enter servo position...");

}
 
void loop() {

  if (Serial.available() > 0) {  
        String input = Serial.readStringUntil('\n');
        input.trim();
        
        targetPos = input.toInt();
        targetPos = constrain((targetPos),0,180);
  
        Serial.print("Moving To: ");
        Serial.println(targetPos);
        Serial.println(" ");
        servo.startEaseTo(targetPos,speed);
        Serial.println("Enter servo position: ");
    }
}
