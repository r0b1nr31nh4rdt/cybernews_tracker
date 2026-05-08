from flask import Flask, request, render_template, make_response
import secrets
from datetime import datetime

app = Flask(__name__)
sessions = {}

@app.route("/")
def return_string():
    return "Welcome to the Route Master Home Page!"

@app.route("/status")
def return_status():
    return "Application is running."

@app.route("/greet/<name>")
def return_greeting(name):
    return f"Hello, {name}!"

@app.route("/calculate/add/<int:num1>/<int:num2>")
def calculate_add(num1, num2):
    result = num1 + num2
    return f"The sum of {num1} and {num2} is {result}."

@app.route("/user/<username>")
def profile(username):
    return render_template("profile.html",
        username=username,
        language="Python",
        hobbies=["Reading", "Gaming", "Traveling"]
    )

@app.route("/loginform")
def login_form():
    return render_template("loginform.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    if username == "admin" and password == "1234":

        session_id = secrets.token_hex(32)

        sessions[session_id] = {
            "username": username,
            "role": "admin",
            "login_time": datetime.now(),
        }

        response = make_response(render_template("index.html"))
        response.set_cookie(
            "session_token",
            session_id,
            httponly=True,
            samesite="Lax",
            secure=True
        )
        return response

    return "Invalid credentials", 401


@app.route("/logout")
def logout():
    session_id = request.cookies.get("session_token")
    if session_id:
        sessions.pop(session_id, None)

    response = make_response(render_template("index.html"))
    response.delete_cookie("session_token")
    return response


@app.route("/cookie_check")
def cookie_check():
    response = make_response(render_template("cookie_check.html"))
    response.set_cookie(
        "visible_cookie",
        "i_am_visible",
        httponly=False,
        samesite="Lax",
        secure=True
    )
    response.set_cookie(
        "hidden_cookie",
        "i_am_hidden",
        httponly=True,
        samesite="Lax",
        secure=True
    )
    return response




if __name__ == "__main__":
    app.run(debug=True)