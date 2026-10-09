"""
Flask Web Application and REST API for Veyra Visual Compiler.
Serves the compiler workspace API and static frontend assets.
"""

import os
from flask import Flask, request, jsonify, send_from_directory
from backend.compiler import VeyraCompiler

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if not os.path.exists(os.path.join(FRONTEND_DIR, "index.html")):
    FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
compiler = VeyraCompiler()

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "examples")


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:path>")
def static_proxy(path):
    if os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "online",
        "service": "Veyra Visual Compiler",
        "phase": 2,
        "academic_title": "Interactive Visual Compiler with Step-by-Step AST and Symbol Table Visualization",
    })


@app.route("/api/compile", methods=["POST"])
def compile_source():
    data = request.get_json(silent=True) or {}
    source = data.get("source") if data.get("source") is not None else data.get("code", "")
    run_interpreter = data.get("run_interpreter", True)

    if not isinstance(source, str):
        return jsonify({"error": "Invalid payload. 'source' must be a string."}), 400

    result = compiler.compile(source=source, run_interpreter=run_interpreter)
    return jsonify(result.to_dict())


@app.route("/api/examples", methods=["GET"])
def get_examples():
    examples = {}
    if os.path.isdir(EXAMPLES_DIR):
        for fname in os.listdir(EXAMPLES_DIR):
            if fname.endswith(".vcl"):
                fpath = os.path.join(EXAMPLES_DIR, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        examples[fname] = f.read()
                except Exception:
                    pass
    return jsonify({"examples": examples})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
