import os
from flask import Flask
from flask_cors import CORS
from .models import db

def create_app():
    app = Flask(__name__)
    CORS(app)

    # ✅ Create folders if they don’t exist
    upload_folder = os.path.join(app.root_path, "..", "data", "uploads")
    parsed_json_folder = os.path.join(app.root_path, "..", "data", "parsed_json")
    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(parsed_json_folder, exist_ok=True)

    # ✅ Set config values
    app.config["UPLOAD_FOLDER"] = upload_folder
    app.config["PARSED_JSON_FOLDER"] = parsed_json_folder

    db.init_app(app)

    from .routes import bp
    app.register_blueprint(bp)

    return app
