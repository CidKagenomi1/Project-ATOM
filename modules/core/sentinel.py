import os
import csv
import time
from datetime import datetime

class Sentinel:
    """The Sentinel: Logging system for AI execution telemetry."""
    def __init__(self, log_file="data/atom_telemetry.csv"):
        self.log_file = log_file
        if not os.path.exists(self.log_file):
            try:
                os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
                with open(self.log_file, mode='w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["timestamp", "user_input", "model_used", "response_time", "status"])
            except Exception as e:
                print(f"[WARN] Sentinel: Could not create local CSV file: {e}")

    def log(self, user_input, model_used, start_time, status="SUCCESS"):
        duration = round(time.time() - start_time, 2)
        try:
            with open(self.log_file, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    user_input[:50] + "...",
                    model_used,
                    duration,
                    status
                ])
        except Exception as e:
            print(f"[LOG ERROR] {e}")
        return duration

