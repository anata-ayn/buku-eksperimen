import os

from flask import Flask, jsonify, send_from_directory

from .api import api


def create_app(database, edit_key=""):
    app = Flask(__name__, static_folder="../static", static_url_path="/static")
    app.config["MAX_CONTENT_LENGTH"] = 32 * 1024
    app.config["EDIT_KEY"] = edit_key
    app.extensions["db"] = database
    app.register_blueprint(api, url_prefix="/api")

    @app.get("/")
    def beranda():
        return send_from_directory(app.static_folder, "index.html")

    @app.get("/healthz")
    def healthz():
        try:
            database.query("SELECT 1 AS ok")
        except Exception:
            return jsonify({"status": "database tidak terjangkau"}), 503
        return jsonify({"status": "ok"})

    @app.after_request
    def header_keamanan(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Referrer-Policy"] = "same-origin"
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        )
        if resp.mimetype in ("application/json",):
            resp.headers["Cache-Control"] = "no-store"
        return resp

    @app.errorhandler(404)
    def tidak_ada(_):
        return jsonify({"error": "Alamat tidak ditemukan."}), 404

    @app.errorhandler(405)
    def metode_salah(_):
        return jsonify({"error": "Metode tidak diizinkan untuk alamat ini."}), 405

    @app.errorhandler(413)
    def terlalu_besar(_):
        return jsonify({"error": "Data yang dikirim terlalu besar (maksimal 32 KB)."}), 413

    return app


def create_app_from_env():
    from .db import database_from_env

    return create_app(database_from_env(), os.environ.get("EDIT_KEY", ""))
