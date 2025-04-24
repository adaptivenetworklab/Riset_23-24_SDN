from flask import Flask, jsonify, request
import os
import json
import time
import threading
import socket
import requests
import random

app = Flask(__name__)

# Configuration
nrf_address = os.environ.get('NRF_ADDRESS', 'nrf')

# IP address management
ip_pool = {f"10.45.0.{i}": None for i in range(2, 254)}  # IP pool excluding .0, .1, .255
allocated_ips = {}
registered = False

# Traffic statistics
traffic_stats = {
    'packets_uplink': 0,
    'packets_downlink': 0,
    'bytes_uplink': 0,
    'bytes_downlink': 0
}

# Register with NRF on startup
def register_with_nrf():
    global registered
    while not registered:
        try:
            response = requests.post(f'http://{nrf_address}/nf/register', json={
                'nf_type': 'upf',
                'nf_id': socket.gethostname(),
                'status': 'active',
                'services': ['user-plane'],
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

def find_available_ip():
    available_ips = [ip for ip, session_id in ip_pool.items() if session_id is None]
    if not available_ips:
        return None
    return random.choice(available_ips)

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({
        'status': 'running',
        'component': 'UPF',
        'registered_with_nrf': registered,
        'allocated_ips': len(allocated_ips),
        'available_ips': len([ip for ip, session_id in ip_pool.items() if session_id is None]),
        'traffic_stats': traffic_stats
    })

@app.route('/ip/allocate', methods=['POST'])
def allocate_ip():
    data = request.json
    session_id = data.get('session_id')
    supi = data.get('supi')

    if not session_id or not supi:
        return jsonify({'error': 'session_id and supi are required'}), 400

    if session_id in allocated_ips:
        return jsonify({
            'ip_address': allocated_ips[session_id],
            'status': 'already_allocated'
        })

    # Allocate IP from pool
    ip_address = find_available_ip()
    if not ip_address:
        return jsonify({'error': 'No IP addresses available in pool'}), 503

    # Update records
    ip_pool[ip_address] = session_id
    allocated_ips[session_id] = ip_address

    return jsonify({
        'ip_address': ip_address,
        'session_id': session_id,
        'supi': supi,
        'allocated_at': time.time()
    })

@app.route('/ip/release', methods=['POST'])
def release_ip():
    data = request.json
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({'error': 'session_id is required'}), 400

    if session_id not in allocated_ips:
        return jsonify({'error': 'Session ID not found in allocated IPs'}), 404

    # Release IP back to pool
    ip_address = allocated_ips[session_id]
    ip_pool[ip_address] = None
    del allocated_ips[session_id]

    return jsonify({
        'ip_address': ip_address,
        'session_id': session_id,
        'status': 'released',
        'released_at': time.time()
    })

@app.route('/traffic/simulate', methods=['POST'])
def simulate_traffic():
    data = request.json
    session_id = data.get('session_id')
    direction = data.get('direction', 'uplink')  # uplink or downlink
    bytes_count = data.get('bytes', 1024)

    if not session_id:
        return jsonify({'error': 'session_id is required'}), 400

    if session_id not in allocated_ips:
        return jsonify({'error': 'Session ID not found in allocated IPs'}), 404

    # Update traffic statistics
    if direction == 'uplink':
        traffic_stats['packets_uplink'] += 1
        traffic_stats['bytes_uplink'] += bytes_count
    else:
        traffic_stats['packets_downlink'] += 1
        traffic_stats['bytes_downlink'] += bytes_count

    return jsonify({
        'session_id': session_id,
        'direction': direction,
        'bytes': bytes_count,
        'ip_address': allocated_ips[session_id],
        'processed_at': time.time(),
        'traffic_stats': traffic_stats
    })

@app.route('/traffic/stats', methods=['GET'])
def get_traffic_stats():
    return jsonify(traffic_stats)

if __name__ == '__main__':
    # Register with NRF on startup
    threading.Thread(target=register_with_nrf, daemon=True).start()

    # Start API server
    app.run(host='0.0.0.0', port=80)
