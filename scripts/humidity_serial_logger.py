import csv
import serial
from datetime import datetime
from collections import deque

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Serial port and output file
SERIAL_PORT = "COM3"         # e.g., COM3, COM4
BAUD_RATE = 115200
OUTPUT_FILE = "humidity_log.csv"

# Number of recent points shown in the live plot
MAX_POINTS = 200

# Data kept for plotting during the measurement
times = deque(maxlen=MAX_POINTS)       # Arduino time_s
humidities = deque(maxlen=MAX_POINTS)  # humidity_rh

ser = None
csv_file = None
csv_writer = None


def init_serial_and_file():
    global ser, csv_file, csv_writer

    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"Opened {SERIAL_PORT} at {BAUD_RATE} baud")
    print(f"Saving to {OUTPUT_FILE}")

    csv_file = open(OUTPUT_FILE, "a", newline="", encoding="utf-8")
    csv_writer = csv.writer(csv_file)

    # Add a header only when the log file is empty.
    if csv_file.tell() == 0:
        csv_writer.writerow(["pc_timestamp", "arduino_time_s", "humidity_rh"])
        csv_file.flush()


def update(frame):
    global ser, csv_writer, csv_file

    # Read a few available serial lines at each plot update.
    for _ in range(10):
        line = ser.readline().decode("utf-8", errors="ignore").strip()
        if not line:
            continue

        # Ignore the CSV header printed by the Arduino.
        if line.startswith("time_s"):
            print(f"[HEADER] {line}")
            continue

        parts = line.split(",")
        if len(parts) != 2:
            print(f"[SKIP] {line}")
            continue

        try:
            arduino_time_s = float(parts[0])
            humidity_rh = float(parts[1])
        except ValueError:
            print(f"[PARSE ERROR] {line}")
            continue

        pc_timestamp = datetime.now().isoformat(timespec="seconds")

        # Save the humidity value to the CSV log.
        csv_writer.writerow([pc_timestamp, arduino_time_s, humidity_rh])
        csv_file.flush()

        # Keep the latest data points for plotting.
        times.append(arduino_time_s)
        humidities.append(humidity_rh)

        print(f"{pc_timestamp} | t={arduino_time_s:.2f}s | RH={humidity_rh:.2f}%")

    # Refresh the live humidity plot.
    ax.clear()
    ax.plot(times, humidities)
    ax.set_title("Real-time Humidity")
    ax.set_xlabel("Arduino Time (s)")
    ax.set_ylabel("Humidity (%RH)")
    ax.grid(True)

    if humidities:
        current_rh = humidities[-1]
        ax.text(
            0.02, 0.95,
            f"Current RH: {current_rh:.2f}%",
            transform=ax.transAxes,
            verticalalignment="top"
        )


def cleanup():
    global ser, csv_file
    if ser is not None and ser.is_open:
        ser.close()
        print("Serial port closed.")
    if csv_file is not None and not csv_file.closed:
        csv_file.close()
        print("CSV file closed.")


if __name__ == "__main__":
    try:
        init_serial_and_file()

        fig, ax = plt.subplots()
        ani = FuncAnimation(fig, update, interval=500, cache_frame_data=False)

        plt.show()

    except KeyboardInterrupt:
        print("\nStopped by user.")

    finally:
        cleanup()
