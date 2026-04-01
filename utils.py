import os
import csv
import uuid
from datetime import datetime, timezone

LOG_DIR = 'logs'


def generate_id(prefix: str) -> str:
    """Generates a unique ID with a given prefix using timestamp + random suffix to avoid collisions."""
    utc_now = datetime.now(timezone.utc)
    suffix = uuid.uuid4().hex[:6]
    return f"{prefix}{utc_now.strftime('%Y%m%d%H%M%S')}{suffix}"


def log_id(id_type: str, unique_id: str):
    """Logs the generated ID to a CSV file in the logs directory."""
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, f"{id_type.lower()}_log.csv")
    file_exists = os.path.isfile(log_file)
    with open(log_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Type", "ID", "Generated_UTC"])
        writer.writerow([id_type.upper(), unique_id, datetime.now(timezone.utc).isoformat()])
