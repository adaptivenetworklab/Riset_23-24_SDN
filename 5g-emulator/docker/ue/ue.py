from flask import Flask, jsonify, request
import os
import json
import time
import threading
import socket
import requests
import random

app = Flask(__name__)

# UE configuration
imsi = os.environ.get('IMSI', f'001010123456789')
gnb_address = os.environ.get('GNB_ADDRESS', 'gnb')
connection_status = 'disconnected'
ip_address = None

# Connect to gNB on startup
def connect_to_gnb():
    global connection_status, ip_address
    try:
        response = requests.post(f'http://{gnb_address}/ue/connect', json={
            'imsi': imsi
        })
        if response.status_code == 200:
            print(f"Successfully connected to gNB: {response.json()}")
            connection_status = 'connected'
            # Simulate getting an IP address from the network
            ip_address = f"10.45.{random.randint(0, 255)}.{random.randint(1, 254)}"
        else:
            print(f"Failed to connect to gNB: {response.text}")
            connection_status = 'failed'
    except Exception as e:
        print(f"Error connecting to gNB: {str(e)}")
        connection_status = 'error'

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({
        'status': 'running',
        'component': 'UE',
        'imsi': imsi,
        'connection_status': connection_status,
        'ip_address': ip_address
    })

@app.route('/traffic/generate', methods=['POST'])
def generate_traffic():
    if connection_status != 'connected':
        return jsonify({'error': 'UE not connected to network'}), 400

    data = request.json
    target = data.get('target', 'upf')
    traffic_type = data.get('type', 'http')
    size = data.get('size', 1024)  # in bytes

    # Simulate traffic generation
    result = {
        'source': imsi,
        'source_ip': ip_address,
        'target': target,
        'type': traffic_type,
        'size': size,
        'timestamp': time.time(),
        'status': 'sent'
    }

    return jsonify(result)

if __name__ == '__main__':
    # Connect to gNB on startup
    threading.Thread(target=connect_to_gnb).start()

    # Start API server
    app.run(host='0.0.0.0', port=80)
