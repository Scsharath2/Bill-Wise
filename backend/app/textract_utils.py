import json
import os
from flask import current_app

def read_parsed_json(filename):
    file_path = os.path.join(current_app.config["PARSED_JSON_FOLDER"], filename)
    print(f"[DEBUG] Reading file from: {file_path}")  # 👈 Add this
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
