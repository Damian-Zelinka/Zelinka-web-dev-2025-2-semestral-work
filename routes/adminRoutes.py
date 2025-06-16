from flask import Blueprint, request, jsonify
from decorators import admin_required
from extensions import db
from models import User, Landmark, Comment, Reaction

admin_bp = Blueprint('admin', __name__)


@admin_bp.route("/delete_comment", methods=["DELETE"])
@admin_required
def delete_comment():
    try:
        data = request.get_json()
        comment_id = data.get("comment_id")


        comment = Comment.query.get(comment_id)
        
        if not comment:
            return jsonify({"message": "Comment not found"}), 404

        db.session.delete(comment)
        db.session.commit()

        return jsonify({"message": "Comment deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error deleting comment: {str(e)}"}), 500


@admin_bp.route("/delete_landmark", methods=["DELETE"])
@admin_required
def delete_landmark():
    try:
        data = request.get_json()
        landmark_id = data.get("landmark_id")
        landmark = Landmark.query.get(landmark_id)
        if not landmark:
            return jsonify({"message": "Landmark not found"}), 404

        Reaction.query.filter_by(landmark_id=landmark_id).delete()

        Comment.query.filter_by(landmark_id=landmark_id).delete()

        db.session.delete(landmark)
        db.session.commit()

        return jsonify({"message": "Landmark and all related data deleted"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error deleting landmark: {str(e)}"}), 500


@admin_bp.route("/delete_user", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    try:
        data = request.get_json()
        deleted_user_id = data.get("user_id")
        if deleted_user_id == user_id:
            return jsonify({"message": "Admins cannot delete themselves"}), 403

        user = User.query.get(deleted_user_id)
        if not user:
            return jsonify({"message": "User not found"}), 404

        for reaction in user.reactions:
            db.session.delete(reaction)

        Comment.query.filter_by(user_id=user_id).delete()
        

        for landmark in user.landmarks:
            for reaction in landmark.reactions:
                db.session.delete(reaction)
            Comment.query.filter_by(landmark_id=landmark.id).delete()
            db.session.delete(landmark)

        db.session.delete(user)
        db.session.commit()

        return jsonify({"message": "User and all related data deleted"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error deleting user: {str(e)}"}), 500