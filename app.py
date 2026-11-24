from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import check_password_hash
from functools import wraps
import json
import socket
import os

app = Flask(__name__)
# Cambia esta clave larga por una propia y privada.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "CAMBIA-ESTA-CLAVE-LARGA-ANTES-DE-PUBLICAR")

# ===== DATOS DE INICIO DE SESIÓN: MODIFICA AQUÍ =====
USUARIO = "carro"

# Hash de ejemplo para la contraseña inicial: Parking2026!
# Genera uno nuevo siguiendo las instrucciones del README.
CONTRASENA_HASH = "scrypt:32768:8:1$1SnMWGCy72C9MvTN$a99d8b8cc5e918559cb6a17fc3f28655dd32ff8493c28f643c08d750509f27c025863fea7138688dfa2c7be9aaf665196441e69f985b4221abfaaf67703a4fde"
# ================================================

TCP_HOST = "127.0.0.1"
TCP_PORT = 5001


def tcp_request(message):
    try:
        with socket.create_connection((TCP_HOST, TCP_PORT), timeout=3) as client:
            client.sendall((message + "\n").encode("utf-8"))
            client.settimeout(3)
            data = b""
            while b"\n" not in data:
                chunk = client.recv(4096)
                if not chunk:
                    break
                data += chunk
            if not data:
                return {"ok": False, "conectado": False, "mensaje": "Sin respuesta del servidor TCP"}
            return json.loads(data.decode("utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "conectado": False, "mensaje": f"Error de comunicación: {exc}"}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "usuario" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("usuario", "")
        password = request.form.get("contrasena", "")
        if username == USUARIO and check_password_hash(CONTRASENA_HASH, password):
            session.clear()
            session["usuario"] = username
            return redirect(url_for("panel"))
        return render_template("index.html", error="Usuario o contraseña incorrectos")
    return render_template("index.html")


@app.route("/panel")
@login_required
def panel():
    return render_template("panel.html")


@app.route("/estado")
@login_required
def estado():
    return jsonify(tcp_request("STATUS"))


@app.route("/comando", methods=["POST"])
@login_required
def comando():
    data = request.get_json(silent=True) or {}
    action = data.get("accion", "")
    if action not in {"OPEN", "CLOSE", "EXIT", "AUTO"}:
        return jsonify({"ok": False, "mensaje": "Acción no válida"}), 400
    result = tcp_request(action)
    return jsonify(result), (200 if result.get("ok") else 503)


@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    # Para una prueba local/túnel. Para producción usa un servidor WSGI.
    app.run(host="127.0.0.1", port=5000, debug=False)
