from flask import Flask
app = Flask(__name__)

@app.route("/")
def index():
    return "hardened-api: lab target following security best practices"

@app.route("/health")
def health():
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
