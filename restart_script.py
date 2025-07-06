import subprocess
import time

while True:
    print("Starting main.py...")
    # Run the main.py script as a subprocess
    process = subprocess.Popen(["python3", "main.py"])

    # Wait for the process to finish (main.py exits)
    process.wait()

    print("main.py has ended. Restarting...")
    time.sleep(1)  # Optionally wait for 1 second before restarting

