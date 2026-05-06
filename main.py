from flask import Flask

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

if __name__ == "__main__":
    app.run(debug=True)