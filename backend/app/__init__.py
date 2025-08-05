import os
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from app.models import db

def create_app():
    app = Flask(__name__)

    # ✅ Define the absolute base path correctly
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # ✅ Set all paths with absolute locations
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(BASE_DIR, "data", "bills.db"),
        UPLOAD_FOLDER=os.path.join(BASE_DIR, "data", "uploads"),
        PARSED_JSON_FOLDER=os.path.join(BASE_DIR, "data", "parsed_json")
    )

    db.init_app(app)
    CORS(app)

    from app.routes import bp
    app.register_blueprint(bp)

    return app
