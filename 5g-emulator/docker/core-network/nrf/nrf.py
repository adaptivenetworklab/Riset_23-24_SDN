from flask import Flask, jsonify, request
import os
import json
import time
import threading
import socket

app = Flask(__name__)

# Store registered NFs
network_functions = {}
heartbeat_timestamps = {}

# NF health check thread
def check_nf_health():
    while True:
        current_time = time.time()
        for nf_id, timestamp in list(heartbeat_timestamps.items()):
            # If no heartbeat for more than 30 seconds, mark as inactive
            if current_time - timestamp > 30:
                if nf_id in network_functions:
                    network_functions[nf_id]['status'] = 'inactive'
                    print(f"NF {nf_id} marked as inactive due to missed heartbeats")

        # Sleep for 10 seconds before next check
        time.sleep(10)

@app.route('/status', methods=['GET'])
def get_status():
    active_nfs = sum(1 for nf in network_functions.values() if nf['status'] == 'active')

    return jsonify({
        'status': 'running',
        'component': 'NRF',
        'registered_nfs': len(network_functions),
        'active_nfs': active_nfs,
        'nf_types': list(set(nf['nf_type'] for nf in network_functions.values()))
    })

@app.route('/nf/register', methods=['POST'])
def register_nf():
    data = request.json
    nf_type = data.get('nf_type')
    nf_id = data.get('nf_id')

    if not nf_type or not nf_id:
        return jsonify({'error': 'nf_type and nf_id are required'}), 400

    # Register the network function
    network_functions[nf_id] = {
        'nf_type': nf_type,
        'nf_id': nf_id,
        'status': data.get('status', 'active'),
        'services': data.get('services', []),
        'api_prefix': data.get('api_prefix', ''),
        'registered_at': time.time()
    }

    # Update heartbeat timestamp
    heartbeat_timestamps[nf_id] = time.time()

    return jsonify({
        'nf_id': nf_id,
        'status': 'registered',
        'timestamp': time.time()
    })

@app.route('/nf/update', methods=['PUT'])
def update_nf():
    data = request.json
    nf_id = data.get('nf_id')

    if not nf_id:
        return jsonify({'error': 'nf_id is required'}), 400

    if nf_id not in network_functions:
        return jsonify({'error': 'Network function not found'}), 404

    # Update the network function
    for key, value in data.items():
        if key != 'nf_id' and key != 'registered_at':
            network_functions[nf_id][key] = value

    # Update heartbeat timestamp
    heartbeat_timestamps[nf_id] = time.time()

    return jsonify({
        'nf_id': nf_id,
        'status': 'updated',
        'timestamp': time.time()
    })

@app.route('/nf/heartbeat', methods=['POST'])
def nf_heartbeat():
    data = request.json
    nf_id = data.get('nf_id')

    if not nf_id:
        return jsonify({'error': 'nf_id is required'}), 400

    if nf_id not in network_functions:
        return jsonify({'error': 'Network function not found'}), 404

    # Update heartbeat timestamp
    heartbeat_timestamps[nf_id] = time.time()

    # If NF was inactive, mark as active again
    if network_functions[nf_id]['status'] == 'inactive':
        network_functions[nf_id]['status'] = 'active'

    return jsonify({
        'nf_id': nf_id,
        'status': 'heartbeat_acknowledged',
        'timestamp': time.time()
    })

@app.route('/nf/deregister', methods=['POST'])
def deregister_nf():
    data = request.json
    nf_id = data.get('nf_id')

    if not nf_id:
        return jsonify({'error': 'nf_id is required'}), 400

    if nf_id not in network_functions:
        return jsonify({'error': 'Network function not found'}), 404

    # Remove the network function
    del network_functions[nf_id]

    # Remove heartbeat timestamp
    if nf_id in heartbeat_timestamps:
        del heartbeat_timestamps[nf_id]

    return jsonify({
        'nf_id': nf_id,
        'status': 'deregistered',
        'timestamp': time.time()
    })

@app.route('/nf/discover', methods=['GET'])
def discover_nf():
    nf_type = request.args.get('nf_type')

    if not nf_type:
        return jsonify({'error': 'nf_type query parameter is required'}), 400

    # Find all active NFs of the requested type
    matching_nfs = [
        nf for nf in network_functions.values()
        if nf['nf_type'] == nf_type and nf['status'] == 'active'
    ]

    if not matching_nfs:
        return jsonify({'error': f'No active network functions of type {nf_type} found'}), 404

    return jsonify({
        'nf_type': nf_type,
        'network_functions': matching_nfs,
        'timestamp': time.time()
    })

@app.route('/nf/list', methods=['GET'])
def list_nfs():
    # Optional filter by type
    nf_type = request.args.get('nf_type')

    if nf_type:
        filtered_nfs = {
            nf_id: nf for nf_id, nf in network_functions.items()
            if nf['nf_type'] == nf_type
        }
        return jsonify(filtered_nfs)

    return jsonify(network_functions)

if __name__ == '__main__':
    # Start health check thread
    health_thread = threading.Thread(target=check_nf_health, daemon=True)
    health_thread.start()

    # Start API server
    app.run(host='0.0.0.0', port=80)
