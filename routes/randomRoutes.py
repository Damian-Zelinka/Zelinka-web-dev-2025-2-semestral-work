from flask import Blueprint, request, jsonify, current_app
from decorators import token_required
from config import ALLOWED_EXTENSIONS
from extensions import db
from models import User


random_bp = Blueprint('random', __name__)


########################################################################## we only allow "png", "jpg", "jpeg", "gif"
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


########################################################################## upload profile picture endpoint
@random_bp.route('/profile_picture', methods=['PUT'])
@token_required
def update_profile_picture(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"message": "User not found"}), 404

        if "image" not in request.files:
            return jsonify({"message": "No image uploaded"}), 400
    
        file = request.files["image"]
        if file.filename == "" or not allowed_file(file.filename):
            return jsonify({"message": "Invalid image file"}), 400

        # Read file data and type
        image_data = file.read()
        mime_type = file.mimetype

        # Update user record
        user.profile_picture_data = image_data
        user.profile_picture_type = mime_type
        
        db.session.commit()

        return jsonify({
            "message": "Profile picture updated",
            "profile_picture": user.get_profile_picture_url()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500



########################################################################## change name / surname  endpoint
@random_bp.route('/change_info', methods=['PUT'])
@token_required
def change_info(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"message": "User not found"}), 404

        data = request.get_json()
        firstName = data.get("name")
        lastName = data.get("surname")

        if firstName is not None:
            user.first_name = firstName
        if lastName is not None:
            user.last_name = lastName

        db.session.commit()

        return jsonify({
            "message": "Data updated",
            "name": user.first_name,
            "surname": user.last_name
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500