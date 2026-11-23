import os
from flask import Flask, jsonify

app = Flask(__name__)

VERSION = os.getenv("APP_VERSION", "v1")
RELEASE_MESSAGE = os.getenv(
    "RELEASE_MESSAGE",
    "Release Pipeline application is running"
)

@app.get("/")
def home():
    return jsonify({
        "application": "Release Pipeline",
        "version": VERSION,
        "message": RELEASE_MESSAGE
    })

@app.get("/health")
def health():
    return jsonify({
        "status": "healthy",
        "version": VERSION
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
