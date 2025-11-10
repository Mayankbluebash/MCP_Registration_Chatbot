# ============================
# ✅ tools/add_registration.py
# ============================
import csv
import os

def add_registration(name: str, email: str, date: str):
    """
    Add a new registration entry with name, email, and date (YYYY-MM-DD).
    """
    file_path = "user_registrations.csv"
    header = ["Name", "Email", "Date"]

    # Create CSV if not exists
    if not os.path.exists(file_path):
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)

    # Append new registration
    with open(file_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([name, email, date])

    return {"message": f"✅ Registration added for {name} on {date}."}
