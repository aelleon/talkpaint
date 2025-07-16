import serial
import time
import serial.tools.list_ports

# ARDUINO_PORT = '/dev/cu.usbserial-2120' # <<< --- CHANGE THIS LINE TO YOUR CORRECT PORT

def find_arduino_port():
    """Finds the serial port for an Arduino device on macOS."""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "usbserial" in port.device: # Typical for Arduino on macOS
            return port.device
    return None

def win(): 
    try: 
        ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
        time.sleep(2) # Give the Arduino time to reset after opening serial

        if ARDUINO_PORT is None:
            print("Arduino not found. Please check if it's plugged in and try again.")
            print("Available ports:")
            for port in serial.tools.list_ports.comports():
                print(f"  {port.device} - {port.description}")
            exit()
        ser.write("win\n".encode()) # Send 'win' command to Arduino
        response = ser.readline().decode().strip()
    except serial.SerialException as e:
        print(f"Error: Could not open serial port {ARDUINO_PORT}. {e}")
        print("Common issues: Arduino IDE Serial Monitor is open, incorrect port, or Arduino not plugged in.")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Serial port closed.")

# --- Configuration ---
ARDUINO_PORT = find_arduino_port()
BAUD_RATE = 9600
# --------------------


# try:
#     ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
#     time.sleep(2) # Give the Arduino time to reset after opening serial

#     print(f"Connected to Arduino on {ARDUINO_PORT} at {BAUD_RATE} baud.")
#     print("Enter servo angles (0-180). Type 'q' to quit.")
#     print("NOTE: Arduino will only process the FIRST valid command with this code.")

#     while True:
#         try:
#             angle_str = input("Enter servo angle (0-180): ")
#             if angle_str.lower() == 'q':
#                 break

#             try:
#                 angle = int(angle_str)
#                 if 0 <= angle <= 180:
#                     command = str(angle) + '\n'
#                     ser.write(command.encode())
#                     print(f"Sent: {angle}")

#                     response = ser.readline().decode().strip()
#                     if response:
#                         print(f"Arduino says: {response}")
#                 else:
#                     print("Angle must be between 0 and 180.")
#             except ValueError:
#                 print("Invalid input. Please enter a number.")

#         except KeyboardInterrupt:
#             print("\nExiting program.")
#             break

# except serial.SerialException as e:
#     print(f"Error: Could not open serial port {ARDUINO_PORT}. {e}")
#     print("Common issues: Arduino IDE Serial Monitor is open, incorrect port, or Arduino not plugged in.")
