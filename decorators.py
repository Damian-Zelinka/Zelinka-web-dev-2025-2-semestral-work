from functools import wraps
from flask import request, jsonify, current_app  
import jwt
from extensions import db
from models import User


########################################################################## token_requred function
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get("access_token")
        if not token:
            return jsonify({"message": "Token is missing!"}), 401
        try:
            data = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"]
                )
            user_id = data["user_id"]
 
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token!"}), 401

        return f(user_id, *args, **kwargs)
    return decorated



########################################################################## admin_required function
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get("access_token")

        if not token:
            return jsonify({"message": "Token is missing!"}), 401
        try:
            data = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"]
            )
            user_id = data["user_id"]
            user = db.session.get(User, user_id)

            if not user:
                return jsonify({"message": "User not found!"}), 401

            if user.status != 'admin':
                return jsonify({"message": "Action reserved for admin only!"}), 403

        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token!"}), 401
        except Exception as e:
            return jsonify({"message": "Error verifying admin status"}), 500

        return f(user_id, *args, **kwargs)
    return decorated



########################################################################## token_optional function
def token_optional(f):
    @wraps(f) # co je toto    ########################################################################################################
    def decorated(*args, **kwargs):
        token = request.cookies.get("access_token")
        user_id = None
        
        if token:
            try:
                data = jwt.decode(
                    token,
                    current_app.config["SECRET_KEY"],
                    algorithms=["HS256"]
                )
                user_id = data["user_id"]
            except jwt.ExpiredSignatureError:
                return jsonify({"message": "Token has expired!"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"message": "Invalid token!"}), 401
        
        return f(user_id, *args, **kwargs)
    
    return decorated