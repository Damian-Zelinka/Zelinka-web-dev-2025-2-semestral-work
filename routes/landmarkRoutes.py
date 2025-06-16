from flask import Blueprint, request, jsonify, current_app
from decorators import token_optional, token_required
from extensions import db
from config import ALLOWED_EXTENSIONS
from models import Landmark, Comment, Reaction
import datetime

landmarks_bp = Blueprint('landmarks', __name__)


########################################################################## we only allow "png", "jpg", "jpeg", "gif"
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS



########################################################################## get all landmarks endpoint
@landmarks_bp.route("/landmarks", methods=["GET"])
@token_optional
def get_landmarks(user_id):
    landmarks = Landmark.query.all()
    
    interactions = {}
    if user_id:
        user_reactions = Reaction.query.filter_by(user_id=user_id).all()
        interactions = {reaction.landmark_id: reaction.value for reaction in user_reactions}

    for landmark in landmarks:
        landmark.comments.sort(key=lambda c: c.date_of_creation, reverse=True)
    
    return jsonify({
        "landmarks": [landmark.to_json() for landmark in landmarks],
        "interactions": interactions
    })



########################################################################## create new landmark endpoint
@landmarks_bp.route("/newlandmark", methods=["POST"])
def create_landmark():
    if "image" not in request.files:
        return jsonify({"message": "No image uploaded"}), 400
    
    file = request.files["image"]
    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"message": "Invalid image file"}), 400

    # Read image data and store in database
    image_data = file.read()
    mime_type = file.mimetype

    name = request.form.get("name")
    description = request.form.get("description")
    likes = request.form.get("likes", 0)
    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")
    user_id = request.form.get("user_id")

    if not all([name, description, latitude, longitude, user_id]):
        return jsonify({"message": "Missing required fields"}), 400

    landmark = Landmark(
        name=name,
        description=description,
        image_data=image_data,
        mime_type=mime_type,
        likes=likes,
        latitude=latitude,
        longitude=longitude,
        user_id=user_id
    )

    try:
        db.session.add(landmark)
        db.session.commit()
        return jsonify(landmark.to_json()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500



########################################################################## create new comment endpoint
@landmarks_bp.route('/comment', methods=['POST'])
@token_required
def add_comment(user_id):

    data = request.get_json()
    text = data.get('text')
    landmark_id = data.get('landmark_id')

    if not all([text, landmark_id, user_id]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        comment = Comment(
            text=text,
            landmark_id=landmark_id,
            user_id=user_id,
            date_of_creation=datetime.datetime.utcnow()
        )
        db.session.add(comment)
        db.session.commit()
        return jsonify({"message": "Comment added", "comment": comment.to_json()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500



########################################################################## like or dislike endpoint
@landmarks_bp.route('/reaction', methods=['POST'])
@token_required
def handle_reaction(user_id):
    data = request.get_json()
    reaction_value = data.get('reaction')
    landmark_id = data.get('landmark_id')
    
    if reaction_value not in ['like', 'dislike', None]:
        return jsonify({"message": "Invalid reaction type"}), 400

    existing = Reaction.query.filter_by(
        user_id=user_id,
        landmark_id=landmark_id
    ).first()

    try:

        if reaction_value is None:
            existing = Reaction.query.filter_by(user_id=user_id, landmark_id=landmark_id).first()
            if existing:
                db.session.delete(existing)
                db.session.commit()
                return jsonify({"message": "Reaction removed"}), 200
            else:
                return jsonify({"message": "No existing reaction to remove"}), 200



        elif existing:
            existing.value = reaction_value
        else:
            new_reaction = Reaction(
                user_id=user_id,
                landmark_id=landmark_id,
                value=reaction_value
            )
            db.session.add(new_reaction)

        db.session.commit()
        return jsonify({
            "message": "Reaction updated successfully",
            "current_reaction": existing.value if existing else None
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500


########################################################################## endpoint to get user's reaction on a specific landmark
@landmarks_bp.route("/interacted", methods=["GET"])
@token_required
def interacted(user_id):

    data = request.get_json()
    landmark_id = data.get("landmark_id")
    
    landmark = Landmark.query.get(landmark_id)
    if not landmark:
        return jsonify({"error": "Landmark not found"}), 404
    
    reaction = Reaction.query.filter_by(
        user_id=user_id,
        landmark_id=landmark_id
    ).first()

    return jsonify({
        "landmark_id": landmark_id,
        "user_reaction": reaction.value if reaction else None
    })