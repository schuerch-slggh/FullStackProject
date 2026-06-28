from flask import Flask


def create_app():
    app = Flask(__name__)

    # Define a route for the homepage
    @app.route("/")
    def hello_world():
        return "Hello, World!"

    return app
