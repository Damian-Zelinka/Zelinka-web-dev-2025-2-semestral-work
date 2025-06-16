from flask import Blueprint, make_response, request, jsonify, current_app
from decorators import admin_required
import jwt
from extensions import db
from models import User, Landmark
import datetime
from datetime import timedelta, timezone


auth_bp = Blueprint('auth', __name__)

########################################################################## get all users endpoint
@auth_bp.route("/users", methods=["GET"])
@admin_required
def get_users(user_id):
    users = User.query.all()
    json_users = list(map(lambda x: x.to_json(), users))
    return jsonify({"users": json_users})



########################################################################## register new user endpoint
@auth_bp.route("/register", methods=["POST"])
def register():

    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    if not username or not password or not email:
        return jsonify({"message": "Some data is missing!"}), 400
    
    new_user = User(username=username, password=password, email=email)
    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        return jsonify({"message": str(e)}), 400
    
    return jsonify({"message": "User created!"}), 201



########################################################################## login endpoint
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() if request.is_json else request.form
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Missing email or password"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or password != user.password:
        return jsonify({"message": "Invalid credentials"}), 401

    expiration_time = datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=1)

    token = jwt.encode(
        {
            "user_id": user.id,
            "exp": expiration_time,
            "iat": datetime.datetime.now(timezone.utc)
        },
        current_app.config["SECRET_KEY"],
        algorithm="HS256",
        
    )
    response = make_response(jsonify({"message": "Login successful!"}))
    response.set_cookie("access_token", token, httponly=True, secure=True, samesite="None")
    return response



########################################################################## logout endpoint
@auth_bp.route("/logout", methods=["POST"])
def logout():
    response = make_response(jsonify({"message": "Logged out"}))
    response.set_cookie("access_token", "", expires=datetime.utcnow() - timedelta(days=1), httponly=True, secure=True, samesite="None")
    return response



########################################################################## endpoint that checks whether user is authenticated
@auth_bp.route("/check_auth", methods=["GET"])
def check_auth():
    token = request.cookies.get("access_token")
    if not token:
        return jsonify({"loggedIn": False}), 200

    try:
        data = jwt.decode(
            token,
            current_app.config["SECRET_KEY"],
            algorithms=["HS256"]
        )
        exp = datetime.datetime.fromtimestamp(data['exp'], tz=timezone.utc)
        iat = datetime.datetime.fromtimestamp(data['iat'], tz=timezone.utc)

        if exp < datetime.datetime.now(timezone.utc):
            response = make_response(jsonify({"loggedIn": False, "message": "Token expired!"}), 401)
            response.set_cookie("access_token", "", expires=0, httponly=True, secure=False, domain="localhost")
            return response

        user_id = data["user_id"]
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({"message": "User not found!"}), 404

        user_landmarks = Landmark.query.filter_by(user_id=user_id).all()
        json_user_landmarks = list(map(lambda x: x.to_json(), user_landmarks))

        return jsonify({
            "loggedIn": True,
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "firstName": user.first_name,
            "lastName": user.last_name,
            "status": user.status,
            "profile_picture": user.get_profile_picture_url(),
            "user_landmarks": json_user_landmarks
        })

    except jwt.ExpiredSignatureError:
        response = make_response(jsonify({"loggedIn": False, "message": "Token expired!"}), 401)
        response.set_cookie("access_token", "", expires=0, httponly=True, secure=False, domain="localhost")
        return response
    except jwt.InvalidTokenError:
        return jsonify({"loggedIn": False, "message": "Invalid token!"}), 401
