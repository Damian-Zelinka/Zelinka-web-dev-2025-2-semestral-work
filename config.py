# config.py
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os
from extensions import db, migrate

load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost:5173"])

app.secret_key = os.getenv("SECRET_KEY")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///semestral.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

db.init_app(app)
migrate.init_app(app, db)

from routes.authRegRoutes import auth_bp
from routes.landmarkRoutes import landmarks_bp
from routes.adminRoutes import admin_bp
from routes.randomRoutes import random_bp

app.register_blueprint(auth_bp)
app.register_blueprint(landmarks_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(random_bp)