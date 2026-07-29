import cv2
import serial
import time
import json
import threading

try:
    from inference_sdk import InferenceHTTPClient
except Exception as e:
    InferenceHTTPClient = None
    INFERENCE_IMPORT_ERROR = e
else:
    INFERENCE_IMPORT_ERROR = None

# --- CONFIGURATION ---
SERIAL_PORT = "COM11"  # Linux: '/dev/ttyUSB0' or '/dev/ttyACM0'
BAUD_RATE = 115200
CAMERA_INDEX = 0
WINDOW_TITLE = "Automated Plant Disease Detection System"

# Roboflow Configuration
ROBOFLOW_API_KEY = "RRGI68pRCISZgtlH2535"
ROBOFLOW_API_URL = "https://serverless.roboflow.com"
WORKSPACE_NAME = "sanjeevs-workspace-uhzdr"
WORKFLOW_ID = "general-segmentation-api"
TARGET_CLASSES = "Tomato leaf, Apple leaf, grape leaf, Strawberry leaf, Peach leaf"

# Motion Parameters
STEPPER_DELTA = 50   # Steps per keyboard tap
SERVO_DELTA = 5      # Degrees per keyboard tap

class HardwareController:
    def __init__(self, port, baud):
        self.ser = None
        try:
            self.ser = serial.Serial(port, baud, timeout=0.1)
            time.sleep(2)  # Wait for Arduino reset sequence
            print(f"[+] Connected to L293D Shield on {port}")
        except Exception as e:
            print(f"[-] Serial Warning: {e}")
            print("[!] Operating in Simulation Mode (No active serial).")

        self.s1_pos = 90
        self.s2_pos = 90

    def send_cmd(self, cmd: str):
        if self.ser and self.ser.is_open:
            self.ser.write(f"{cmd}\n".encode('utf-8'))

    def move_stepper(self, steps: int):
        self.send_cmd(f"M{steps}")

    def adjust_servo1(self, delta: int):
        self.s1_pos = max(0, min(180, self.s1_pos + delta))
        self.send_cmd(f"S{self.s1_pos}")

    def adjust_servo2(self, delta: int):
        self.s2_pos = max(0, min(180, self.s2_pos + delta))
        self.send_cmd(f"C{self.s2_pos}")

    def close(self):
        if self.ser and self.ser.is_open:
            self.send_cmd("R")  # Reset hardware state
            self.ser.close()


def run_roboflow_inference(image_path: str, client):
    print("\n[+] Triggering Roboflow Cloud Inference...")
    try:
        result = client.run_workflow(
            workspace_name=WORKSPACE_NAME,
            workflow_id=WORKFLOW_ID,
            images={"image": image_path},
            parameters={"classes": TARGET_CLASSES},
            use_cache=True
        )
        print("=== INFERENCE RESULT ===")
        print(json.dumps(result, indent=2))
        print("========================\n")
    except Exception as e:
        print(f"[-] Inference Error: {e}")


def main():
    hw = HardwareController(SERIAL_PORT, BAUD_RATE)

    if InferenceHTTPClient is None:
        client = None
        print(f"[-] Roboflow SDK unavailable: {INFERENCE_IMPORT_ERROR}")
        print("[!] Analysis capture will be disabled until the package is installed.")
    else:
        client = InferenceHTTPClient(api_url=ROBOFLOW_API_URL, api_key=ROBOFLOW_API_KEY)

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("[-] Error: Camera stream unavailable.")
        return

    cv2.namedWindow(WINDOW_TITLE, cv2.WINDOW_NORMAL)
    cv2.moveWindow(WINDOW_TITLE, 100, 100)

    print("""
==================================================
 Plant Scanner Control Terminal (L293D Shield)
--------------------------------------------------
 [A] / [D] or [a] / [d]: Stepper Motor (Left / Right - M3/M4)
 [W] / [S] or [w] / [s]: Servo 1 Base Gimbal (Up / Down - SER1)
 [I] / [K] or [i] / [k]: Servo 2 Camera Tilt (Up / Down - SER2)
 [SPACEBAR]: Capture frame & trigger Roboflow API
 [Q]       : Exit System
==================================================
    """)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[-] Frame grab error.")
            break

        # Render control overlay text
        status_text = f"SER1: {hw.s1_pos} deg | SER2: {hw.s2_pos} deg"
        cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.6, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(frame, "Press SPACE to Analyze", (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2, cv2.LINE_AA)

        cv2.imshow(WINDOW_TITLE, frame)

        key = cv2.waitKey(1) & 0xFF

        # Ignore no-key events and keep the loop responsive.
        if key in (-1, 255):
            continue

        # Spacebar
        if key == 32:
            if client is None:
                print("[-] Roboflow analysis is unavailable because the SDK is not installed.")
                continue

            temp_filename = "temp_plant.jpg"
            cv2.imwrite(temp_filename, frame)
            print(f"[+] Frame saved as {temp_filename}")
            # Non-blocking API call
            threading.Thread(
                target=run_roboflow_inference,
                args=(temp_filename, client),
                daemon=True
            ).start()
            continue

        # Convert key code to character and compare case-insensitively
        try:
            ch = chr(key).lower()
        except Exception:
            ch = ''

        if ch == 'q':
            break
        elif ch == 'a':
            hw.move_stepper(-STEPPER_DELTA)
        elif ch == 'd':
            hw.move_stepper(STEPPER_DELTA)
        elif ch == 'w':
            hw.adjust_servo1(SERVO_DELTA)
        elif ch == 's':
            hw.adjust_servo1(-SERVO_DELTA)
        elif ch == 'i':
            hw.adjust_servo2(SERVO_DELTA)
        elif ch == 'k':
            hw.adjust_servo2(-SERVO_DELTA)

    cap.release()
    cv2.destroyAllWindows()
    hw.close()

if __name__ == "__main__":
    main()