import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    CORS(app)

    # ✅ Absolute paths for folders
    base_dir = os.path.abspath(os.path.join(app.root_path, ".."))
    upload_folder = os.path.join(base_dir, "data", "uploads")
    parsed_json_folder = os.path.join(base_dir, "data", "parsed_json")

    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(parsed_json_folder, exist_ok=True)

    app.config["UPLOAD_FOLDER"] = upload_folder
    app.config["PARSED_JSON_FOLDER"] = parsed_json_folder
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bills.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    from .routes import bp
    app.register_blueprint(bp)

    return app
