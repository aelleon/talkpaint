#include "Arduino.h" 
#include "double_eye.h"

//Servo Connection Pins, Left Eye, then Right Eye (Left Right, Up Down, Open Close) 
// The order of left and right is important, and it it taken from the robots perspective (use the linkage labels for reference)
Eyes Eyes(10,9,4,
          3,5,6);

void setup() {
  Serial.begin(9600);
  
  // ENTER YOUR VALUES FOR UPPER/LOWER/CENTRE HERE, USE CALIBRATION.INO To Find the Values
// VRight RL Centre/Min/eMax 60/95/120 (Pin 3)
// V Right Blink Close/Open 60/85 (Pin 6)
  Eyes.rightEye.setLeftRightLowerUpperCentre(60,120,95);
  Eyes.rightEye.setUpDownLowerUpperCentre(45,120,85);
  Eyes.rightEye.setEyeLidOpenClose(85,60);

  Eyes.leftEye.setLeftRightLowerUpperCentre(65,130,95);
  Eyes.leftEye.setUpDownLowerUpperCentre(35,110,75);
  Eyes.leftEye.setEyeLidOpenClose(90,120);

  //Setup Eyes
  Eyes.init(); 

  // Centre Eyes
  Eyes.home();
}

void loop() {
  Eyes.eyeMotion(random(200,500));
  someFunction();
}

void someFunction() {
  //Put whatever you want here (non blocking)
}

