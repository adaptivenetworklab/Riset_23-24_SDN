from flask import Flask, jsonify, request
import os
import json
import time
import threading
import socket
import requests

app = Flask(__name__)

# gNB configuration
gnb_id = os.environ.get('GNB_ID', 'gnb-001')
amf_address = os.environ.get('AMF_ADDRESS', 'amf')
connected_ues = {}

# Register with AMF on startup
def register_with_amf():
    try:
        response = requests.post(f'http://{amf_address}/gnb/register', json={
            'gnb_id': gnb_id,
            'ip': socket.gethostbyname(socket.gethostname())
        })
        if response.status_code == 200:
            print(f"Successfully registered with AMF: {response.json()}")
        else:
            print(f"Failed to register with AMF: {response.text}")
    except Exception as e:
        print(f"Error registering with AMF: {str(e)}")

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({
        'status': 'running',
        'component': 'gNB',
        'gnb_id': gnb_id,
        'connected_ues': len(connected_ues)
    })

@app.route('/ue/connect', methods=['POST'])
def connect_ue():
    data = request.json
    imsi = data.get('imsi')

    if not imsi:
        return jsonify({'error': 'imsi is required'}), 400

    # Connect UE locally
    connected_ues[imsi] = {
        'connected_at': time.time(),
        'status': 'connected'
    }

    # Register UE with AMF
    try:
        response = requests.post(f'http://{amf_address}/ue/register', json={
            'imsi': imsi,
            'gnb_id': gnb_id
        })
        if response.status_code == 200:
            return jsonify({'status': 'connected', 'imsi': imsi})
        else:
            # Roll back local connection
            del connected_ues[imsi]
            return jsonify({'error': f"AMF registration failed: {response.text}"}), 500
    except Exception as e:
        # Roll back local connection
        if imsi in connected_ues:
            del connected_ues[imsi]
        return jsonify({'error': f"Error connecting to AMF: {str(e)}"}), 500

if __name__ == '__main__':
    # Register with AMF on startup
    threading.Thread(target=register_with_amf).start()

    # Start API server
    app.run(host='0.0.0.0', port=80)
