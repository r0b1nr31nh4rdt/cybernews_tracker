from flask import Flask, render_template

app = Flask(__name__)

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

if __name__ == "__main__":
    app.run(debug=True)