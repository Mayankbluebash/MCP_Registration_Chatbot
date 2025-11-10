# ============================
# ✅ tools/view_all_registration.py
# ============================
import csv
import os

def view_all_registration():
    """
    Return all registration records as a list of dictionaries.
    """
    file_path = "user_registrations.csv"
    if not os.path.exists(file_path):
        return []

    with open(file_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        data = list(reader)

    clean_data = []
    for row in data:
        if row and any(row.values()):  # Skip empty rows
            clean_row = {k.strip(): v.strip() for k, v in row.items() if k and v}
            clean_data.append(clean_row)

    return clean_data
