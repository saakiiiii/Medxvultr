from functools import wraps
from flask import session, jsonify
from database.db import mongo

def login_user(username, password):
    user = mongo.db.users.find_one({"username": username, "password": password})
    return user

def logout_user():
    session.pop('user_id', None)

def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function
