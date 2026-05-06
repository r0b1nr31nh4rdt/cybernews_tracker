from flask import Flask, render_template, request
from flask_jwt_extended import JWTManager, create_access_token
from database import init_db
from auth import verify_user
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
jwt = JWTManager(app)

@app.route("/")
def hello():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.json.get("username")
    password = request.json.get("password")
    user = verify_user(username, password)
    if user:
        token = create_access_token(identity=user)
        return jsonify(access_token=token)
    return jsonify({"msg": "Invalid credentials"}), 401

if __name__ == "__main__":
    init_db()
    app.run(debug=True)