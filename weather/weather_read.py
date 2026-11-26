import time
import os
from plyer import notification

def read_file_line(file_path):
    with open(file_path, 'r') as file:
        for line in file:
            yield line.strip()

def display_notification(title, message):
    notification.notify(
        title=title,
        message=message,
        app_icon=None,  # e.g. 'path/to/icon.ico'
        timeout=10,  # seconds
    )

def main(file_path):
    line_generator = read_file_line(file_path)
    
    while True:
        try:
            line = next(line_generator)
            display_notification("Daily Notification", line)
            time.sleep(15*60)  # Sleep for 24 hours
        except StopIteration:
            print("Reached the end of the file. Restarting from the beginning.")
            line_generator = read_file_line(file_path)

if __name__ == "__main__":
    file_path = "D:/Github/The-Open-Matrix/plugins/weather/weather_data_2025/weather_simulation.txt"
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
    else:
        main(file_path)