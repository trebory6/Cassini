import socket
import json
import threading
from flask import Flask, jsonify
from websocket import create_connection

app = Flask(__name__)

printer_ip = None
printer_status = {}
ws_connection = None

def discover_printer():
    global printer_ip
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_socket.settimeout(5)

    message = "M99999".encode('utf-8')
    udp_socket.sendto(message, ("<broadcast>", 3000))

    try:
        response, addr = udp_socket.recvfrom(1024)
        printer_ip = addr[0]
        print(f"Printer found at: {printer_ip}")
    except socket.timeout:
        print("Printer not found.")
    finally:
        udp_socket.close()

def connect_to_printer():
    global ws_connection, printer_status
    if not printer_ip:
        print("Printer IP not discovered!")
        return

    try:
        ws_connection = create_connection(f"ws://{printer_ip}:3030/websocket")
        print(f"Connected to printer at {printer_ip}")
        
        while True:
            message = ws_connection.recv()
            data = json.loads(message)
            printer_status = data
            print(f"Received status: {data}")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if ws_connection:
            ws_connection.close()

@app.route('/status', methods=['GET'])
def get_status():
    if not printer_status:
        return jsonify({"error": "No status available"}), 503
    return jsonify(printer_status)

if __name__ == "__main__":
    discover_printer()
    threading.Thread(target=connect_to_printer, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
