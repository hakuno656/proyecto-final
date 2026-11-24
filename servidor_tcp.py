import json
import socket
import threading
import time
import serial

SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 9600
TCP_HOST = "127.0.0.1"
TCP_PORT = 5001

arduino = None
serial_lock = threading.Lock()
state_lock = threading.Lock()

state = {
    "conectado": False,
    "distancia": None,
    "ocupado": False,
    "barrera": False,
    "automatico": True
}

ALLOWED_COMMANDS = {"OPEN", "CLOSE", "EXIT", "AUTO"}


def serial_reader():
    global arduino

    while True:
        try:
            if arduino is None or not arduino.is_open:
                arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
                time.sleep(2)
                with state_lock:
                    state["conectado"] = True
                print(f"Arduino conectado en {SERIAL_PORT}")

            line = arduino.readline().decode("utf-8", errors="ignore").strip()
            if not line.startswith("STATUS,"):
                continue

            parts = line.split(",")
            if len(parts) != 5:
                continue

            with state_lock:
                state.update({
                    "conectado": True,
                    "distancia": float(parts[1]),
                    "ocupado": parts[2] == "1",
                    "barrera": parts[3] == "1",
                    "automatico": parts[4] == "1"
                })

        except (serial.SerialException, OSError, ValueError) as exc:
            print("Comunicación serial:", exc)
            with state_lock:
                state["conectado"] = False
            try:
                if arduino and arduino.is_open:
                    arduino.close()
            except Exception:
                pass
            arduino = None
            time.sleep(3)


def send_command(command):
    if command not in ALLOWED_COMMANDS:
        return {"ok": False, "mensaje": "Comando no válido"}

    with serial_lock:
        if arduino is None or not arduino.is_open:
            return {"ok": False, "mensaje": "Arduino desconectado"}
        try:
            arduino.write((command + "\n").encode("utf-8"))
            return {"ok": True, "mensaje": "Comando enviado"}
        except (serial.SerialException, OSError) as exc:
            return {"ok": False, "mensaje": str(exc)}


def handle_client(conn):
    try:
        conn.settimeout(3)
        raw = conn.recv(1024).decode("utf-8", errors="ignore").strip()
        if raw == "STATUS":
            with state_lock:
                response = dict(state)
        else:
            response = send_command(raw)

        conn.sendall((json.dumps(response) + "\n").encode("utf-8"))
    except Exception as exc:
        print("Error TCP:", exc)
    finally:
        conn.close()


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((TCP_HOST, TCP_PORT))
    server.listen(10)
    print(f"Servidor TCP escuchando en {TCP_HOST}:{TCP_PORT}")

    while True:
        conn, _ = server.accept()
        threading.Thread(target=handle_client, args=(conn,), daemon=True).start()


if __name__ == "__main__":
    threading.Thread(target=serial_reader, daemon=True).start()
    start_server()
