#include <AFMotor.h>
#include <Servo.h>

// Stepper Motor
AF_Stepper stepper(200, 2);   // M3 + M4

// Servo Motors
Servo servo1;
Servo servo2;

int servo1Pos = 90;
int servo2Pos = 90;

void setup()
{
    Serial.begin(9600);

    servo1.attach(9);   // Servo Port 1
    servo2.attach(10);  // Servo Port 2

    servo1.write(servo1Pos);
    servo2.write(servo2Pos);

    stepper.setSpeed(30);

    Serial.println("Robot Arm Ready");
}

void loop()
{
    if (Serial.available())
    {
        char cmd = Serial.read();

        switch(cmd)
        {

            case 'A':
                stepper.step(20, BACKWARD, DOUBLE);
                break;

            case 'D':
                stepper.step(20, FORWARD, DOUBLE);
                break;

            case 'W':
                servo1Pos += 5;
                servo1Pos = constrain(servo1Pos,0,180);
                servo1.write(servo1Pos);
                break;

            case 'S':
                servo1Pos -= 5;
                servo1Pos = constrain(servo1Pos,0,180);
                servo1.write(servo1Pos);
                break;

            case 'I':
                servo2Pos += 5;
                servo2Pos = constrain(servo2Pos,0,180);
                servo2.write(servo2Pos);
                break;

            case 'K':
                servo2Pos -= 5;
                servo2Pos = constrain(servo2Pos,0,180);
                servo2.write(servo2Pos);
                break;

        }

    }

}
