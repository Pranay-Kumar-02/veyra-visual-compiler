"""
Flask Web Application and REST API for Veyra Visual Compiler.
Serves the compiler workspace API and static frontend assets.
Exposes modular endpoints for Compilation, Control Flow Graph,
3AC Optimization, and Step-by-Step Debugging.
Hardened with input validation, request size limits, and security headers.
"""

import os
import re
from flask import Flask, request, jsonify, send_from_directory
from backend.compiler import VeyraCompiler

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if not os.path.exists(os.path.join(FRONTEND_DIR, "index.html")):
    FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
compiler = VeyraCompiler()

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "examples")
MAX_SOURCE_LENGTH = 100_000  # 100 KB max source code size


@app.after_request
def add_security_headers(response):
    """Enforce standard HTTP security headers for production safety."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


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
        "phase": 3,
        "academic_title": "Interactive Visual Compiler with CFG, 3AC Optimization, and Step-by-Step Debugger",
        "features": [
            "Lexer & Parser with AST Visualization",
            "Semantic Analysis & Symbol Table",
            "Three-Address Code Generation",
            "Control Flow Graph Construction & Reachability",
            "Modular 3AC Optimization Pipeline",
            "Step-by-Step Execution Debugger & Trace",
        ],
    })


@app.route("/api/compile", methods=["POST"])
def compile_source():
    try:
        data = request.get_json(silent=True) or {}
        source = data.get("source") if data.get("source") is not None else data.get("code", "")
        run_interpreter = data.get("run_interpreter", True)

        if not isinstance(source, str):
            return jsonify({"error": "Invalid payload. 'source' must be a string."}), 400

        if len(source) > MAX_SOURCE_LENGTH:
            return jsonify({
                "error": f"Payload too large. Source code must not exceed {MAX_SOURCE_LENGTH} characters."
            }), 413

        result = compiler.compile(source=source, run_interpreter=run_interpreter)
        return jsonify(result.to_dict())
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Internal compilation server error",
            "message": str(e),
            "diagnostics": [{
                "stage": "System Error",
                "message": f"Server encountered an unexpected error: {str(e)}",
                "line": 1,
                "column": 1,
                "severity": "error",
                "hint": None,
                "formatted": str(e),
            }],
        }), 500


@app.route("/api/cfg", methods=["POST"])
def get_cfg():
    """Returns the Control Flow Graph generated for the source program."""
    try:
        data = request.get_json(silent=True) or {}
        source = data.get("source") if data.get("source") is not None else data.get("code", "")
        if not isinstance(source, str):
            return jsonify({"error": "Invalid payload. 'source' must be a string."}), 400

        if len(source) > MAX_SOURCE_LENGTH:
            return jsonify({"error": "Payload too large."}), 413

        result = compiler.compile(source=source, run_interpreter=False)
        if not result.success and result.cfg is None:
            return jsonify({
                "success": False,
                "diagnostics": result.diagnostics,
                "cfg": None,
            }), 400

        return jsonify({
            "success": True,
            "cfg": result.cfg,
            "ir_code": result.ir_code,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/optimize", methods=["POST"])
def optimize_ir():
    """Returns original vs optimized 3AC and transformation report."""
    try:
        data = request.get_json(silent=True) or {}
        source = data.get("source") if data.get("source") is not None else data.get("code", "")
        if not isinstance(source, str):
            return jsonify({"error": "Invalid payload. 'source' must be a string."}), 400

        if len(source) > MAX_SOURCE_LENGTH:
            return jsonify({"error": "Payload too large."}), 413

        result = compiler.compile(source=source, run_interpreter=False)
        if not result.success and result.optimization_report is None:
            return jsonify({
                "success": False,
                "diagnostics": result.diagnostics,
                "optimization_report": None,
            }), 400

        return jsonify({
            "success": True,
            "original_ir": result.ir,
            "original_ir_code": result.ir_code,
            "optimized_ir": result.optimized_ir,
            "optimized_ir_code": result.optimized_ir_code,
            "optimization_report": result.optimization_report,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/debug", methods=["POST"])
def debug_trace():
    """Returns the step-by-step execution trace of the AST interpreter."""
    try:
        data = request.get_json(silent=True) or {}
        source = data.get("source") if data.get("source") is not None else data.get("code", "")
        if not isinstance(source, str):
            return jsonify({"error": "Invalid payload. 'source' must be a string."}), 400

        if len(source) > MAX_SOURCE_LENGTH:
            return jsonify({"error": "Payload too large."}), 413

        result = compiler.compile(source=source, run_interpreter=True)
        return jsonify({
            "success": result.success,
            "debug_trace": result.debug_trace,
            "output": result.output,
            "diagnostics": result.diagnostics,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/examples", methods=["GET"])
def get_examples():
    """Safely retrieves sample VCL files without path traversal risks."""
    examples = {}
    if os.path.isdir(EXAMPLES_DIR):
        for fname in sorted(os.listdir(EXAMPLES_DIR)):
            # Strictly validate filename characters to prevent path traversal
            if re.match(r"^[a-zA-Z0-9_\-]+\.vcl$", fname):
                fpath = os.path.join(EXAMPLES_DIR, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        examples[fname] = f.read()
                except Exception:
                    pass
    return jsonify({"examples": examples})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
