from flask import Flask, jsonify, request
import os
import json
import time
import threading
import socket
import requests

app = Flask(__name__)

# Configuration
nrf_address = os.environ.get('NRF_ADDRESS', 'nrf')
upf_address = os.environ.get('UPF_ADDRESS', 'upf')

# Store session contexts
session_contexts = {}
registered = False

# Register with NRF on startup
def register_with_nrf():
    global registered
    while not registered:
        try:
            response = requests.post(f'http://{nrf_address}/nf/register', json={
                'nf_type': 'smf',
                'nf_id': socket.gethostname(),
                'status': 'active',
                'services': ['session-management'],
                'api_prefix': f'http://{socket.gethostname()}'
            })
            if response.status_code == 200:
                print(f"Successfully registered with NRF: {response.json()}")
                registered = True
            else:
                print(f"Failed to register with NRF: {response.text}")
                time.sleep(5)  # Retry after 5 seconds
        except Exception as e:
            print(f"Error registering with NRF: {str(e)}")
            time.sleep(5)  # Retry after 5 seconds

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({
        'status': 'running',
        'component': 'SMF',
        'registered_with_nrf': registered,
        'active_sessions': len(session_contexts)
    })

@app.route('/session/create', methods=['POST'])
def create_session():
    data = request.json
    supi = data.get('supi')
    dnn = data.get('dnn', 'internet')

    if not supi:
        return jsonify({'error': 'supi is required'}), 400

    # Create session ID
    session_id = f'{supi}-{int(time.time())}'

    # Store session context
    session_contexts[session_id] = {
        'supi': supi,
        'dnn': dnn,
        'created_at': time.time(),
        'status': 'created'
    }

    # Request IP address allocation from UPF
    try:
        response = requests.post(f'http://{upf_address}/ip/allocate', json={
            'session_id': session_id,
            'supi': supi
        })

        if response.status_code == 200:
            ip_data = response.json()
            session_contexts[session_id]['ip_address'] = ip_data.get('ip_address')
            session_contexts[session_id]['status'] = 'active'

            return jsonify({
                'session_id': session_id,
                'ip_address': ip_data.get('ip_address'),
                'status': 'active'
            })
        else:
            session_contexts[session_id]['status'] = 'failed'
            return jsonify({'error': f"UPF IP allocation failed: {response.text}"}), 500

    except Exception as e:
        session_contexts[session_id]['status'] = 'failed'
        return jsonify({'error': f"UPF communication error: {str(e)}"}), 500

@app.route('/session/<session_id>', methods=['GET'])
def get_session(session_id):
    if session_id not in session_contexts:
        return jsonify({'error': 'Session not found'}), 404

    return jsonify(session_contexts[session_id])

@app.route('/session/<session_id>/release', methods=['POST'])
def release_session(session_id):
    if session_id not in session_contexts:
        return jsonify({'error': 'Session not found'}), 404

    # Request IP address release from UPF
    try:
        response = requests.post(f'http://{upf_address}/ip/release', json={
            'session_id': session_id
        })

        # Mark session as released regardless of UPF response
        session_contexts[session_id]['status'] = 'released'
        session_contexts[session_id]['released_at'] = time.time()

        return jsonify({
            'session_id': session_id,
            'status': 'released'
        })
    except Exception as e:
        return jsonify({'error': f"UPF communication error: {str(e)}"}), 500

if __name__ == '__main__':
    # Register with NRF on startup
    threading.Thread(target=register_with_nrf, daemon=True).start()

    # Start API server
    app.run(host='0.0.0.0', port=80)
