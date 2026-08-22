from flask import Flask
app = Flask(__name__)

@app.route("/")
def index():
    return "vuln-web: intentionally insecure lab target (runs as root, no limits)"

@app.route("/health")
def health():
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
